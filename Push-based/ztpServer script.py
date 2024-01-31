#############################################################################################################
# This script will upgrade the ios on a cisco device
# Version 1.0
# Author:  Magnus
#############################################################################################################

from netmiko import ConnectHandler
from getpass import getpass
import re
import time
import subprocess
import os

software_mappings = {
    'C9300-24U': {
        'software_image': 'cat9k_iosxe.17.06.06a.SPA.bin',
        'software_version': '17.06.06a',
        'software_md5_checksum': '0af35c3ae22f514e92e223f6a0a257f0',
        'installMethod': 'method1'
    },
    'C9500-24Q': {
        'software_image': 'cat9k_iosxe.17.06.01.SPA.bin',
        'software_version': '17.06.01',
        'software_md5_checksum': 'fdb9c92bae37f9130d0ee6761afe2919',
        'installMethod': 'method1'
    },
    'ASR1001-HX': {
        'software_image': 'asr1000-universalk9.17.05.01a.SPA.bin',
        'software_version': '17.05.01a',
        'software_md5_checksum': '0e4b1fc1448f8ee289634a41f75dc215',
        'installMethod': 'method2'
    },
    'C8000V': {
        'software_image': 'cat9k_iosxe.17.09.04a.SPA.bin',
        'software_version': '17.09.04a',
        'software_md5_checksum': '16a20aa19ec9deb2abe421efddb75fae',
        'installMethod': 'method2'
    }
}


transferProtocol = 'http' #http or tftp
fileServer = '192.168.131.10' #ip address of the file server

doStagingOnly = False
doIosUpgrade = True
#doConfigUpdate = False 

#check what opertatings system device is running the script
if os.name == 'nt':
    thisDevice = 'windows'
else:
    thisDevice = 'linux '  




#function that connects to device
def connectToDevice(ipaddress, username, password):
    print(f'Connecting to device {ipaddress}...')
    device = {
        'device_type': 'cisco_ios',    # Adjust if using a different device type
        'ip': ipaddress,               # IP address of the device
        'username': username,           # Device login username
        'password': password            # Device login password
    }
    # Connect to the device
    net_connect = ConnectHandler(**device)
    net_connect.enable()
    return net_connect


#function that checks if upgrade is required
def CheckIfUpgradeIsRequired(net_connect):
    #get running hardware type
    showVerstionHardware= net_connect.send_command('show  ver | inc isco.*processor ')
    hardwareType = showVerstionHardware.split()[1]
    #print(hardwareType)
    
    #get running software version
    showVersionIos = net_connect.send_command('show  ver | inc re, Version')
    currentVersion = showVersionIos.split()[-1]
    #print(currentVersion)

    #Returns False if on approved version or True if upgrade is required
    if hardwareType not in software_mappings:
        print("Hardware type not found in software_mappings, please add it")
        return False, hardwareType
    print(f"Hardware type is {hardwareType}, running ios is {currentVersion}")
    if (software_mappings[hardwareType]['software_version'] == currentVersion):
        print("No upgrade ios required")
        return False, hardwareType
    else:
        print("Upgrade ios required")   
        return True, hardwareType

#function that checks if there is enough disk space
def CheckDiskSpace(net_connect):
    dirCommand = net_connect.send_command('dir | inc bytes free')
    diskSpace = int(re.findall(r'\d+', dirCommand.split()[3])[0])
    threshold = 1500000 #1.5GB
    if diskSpace < threshold:
        print("Not enough disk space")
        return False
    else:
        print("Enough disk space")
        return True

#function that checks if the ios file exists on flash
def checkFileExists(net_connect, filename):
    fileCheck = net_connect.send_command('dir flash:' + filename)
    if 'No such file or directory' in fileCheck:
        print(f'The IOS does NOT exist on flash')
        return False
    elif 'Directory of ' in fileCheck:
        print(f'The {filename} DOES exist on flash')
        return True
    else:
        print('- Unexpected output from check_file_exists \n')
        raise ValueError("Unexpected output from check_file_exists")


#function that copies the ios file to flash
def copyFileToFlash(net_connect, filename):
    #copy file to flash
    print(f'Copying {filename} to flash...')
    copy_command = f'copy {transferProtocol}://{fileServer}/{filename} flash:'
    #print(copy_command)
    net_connect.send_command(copy_command, expect_string=r'Destination filename')
    output = net_connect.send_command('\n', expect_string=r'#', delay_factor=5, read_timeout=300)
    if "copied" in output:
        print("File successfully copied to flash")
        return True
    else:
        print("File copy failed")
        return False

#function that verifies the md5 checksum of the ios file
def verifyDstImageMd5(net_connect, filename, hardwareType):
    verify_md5 = 'verify /md5 flash:' + filename
    print(verify_md5)
    try:
        verify_md5_output = net_connect.send_command(verify_md5,expect_string=r'#', delay_factor=5, read_timeout=300)
        if software_mappings[hardwareType]['software_md5_checksum'] in verify_md5_output:
            print('MD5 hashes match')
            return True
        else:
            print('MD5 checksum mismatch')
            return False
    except Exception as e:
        print(e)
        print('MD5 checksum failed due to an exception')
        return True  

#function that installs the ios file
def installMethod1(net_connect, filename):
    #install save config
    print('saving running configuraion')
    net_connect.send_command('wr mem', expect_string=r'#', delay_factor=5, read_timeout=10)
    #make a file on flash
    net_connect.send_command('show ver | redirect flash:upgradeInProcess.txt')

    #install image
    print('Installing image...')
    install_command = 'install add file flash:' + filename + ' activate commit'
    print(install_command)
    #net_connect.send_command(install_command, expect_string=r'Do you want to proceed? [y/n]', delay_factor=5, read_timeout=300)
    net_connect.send_command('y')
    time.sleep(60)


#function that installs the ios file
def installMethod2(net_connect, filename):
    #install save config
    print('Creating upgradeInProcess.txt on flash')
    net_connect.send_command('show ver | redirect flash:upgradeInProcess.txt')
    print('Changing boot system variables')
    set_boot = ['no boot system ']
    #set_boot = ['no boot system ',"boot system bootflash:"+filename]
    net_connect.send_config_set(set_boot)
    net_connect.send_command('wr mem', expect_string=r'#', delay_factor=5, read_timeout=10)
    net_connect.send_command('reload', expect_string=r'[confirm]')
    try:
        net_connect.send_command('\n')
    except Exception as e:
        if "Socket is closed" in str(e):
            print("Socket is closed, please wait for the device to reload")
    time.sleep(30)

#function that pings the device to check if it is online
def pingDevice(ipaddress):
    print("Check if the device is online...")
    device_online = False
    while device_online == False:
        if thisDevice == 'windows':
            ping_output = subprocess.run(['ping ', ipaddress], capture_output=True)
            if "Received = 4" in ping_output.stdout.decode():
                print("Device is online")
                device_online = True
                return True
        if thisDevice == 'linux':
            response = subprocess.check_output(["ping", "-c", "1", ipaddress])
            if "1 received" in response.decode():
                print("Device is online")
                device_online = True
                return True
        else:
            print("Device is offline, please wait...")
        time.sleep(120)

#function that clean up after method 1
def cleanUpMethod1(net_connect):
    #clean up
    print('Cleaning up...')
    install_command = 'install remove inactive'
    net_connect.send_command(install_command, expect_string=r'Do you want to proceed? [y/n]', delay_factor=5, read_timeout=300)
    net_connect.send_command('y')
    time.sleep(30)
    net_connect.send_command('delete /force flash:upgradeInProcess.txt', expect_string=r'#')
    print('Cleaning complete')

def cleanUpMethod2(net_connect, filename):
    print('Starting cleanup process...')
    print('Deleting upgradeInProcess.txt')
    net_connect.send_command('delete /force flash:upgradeInProcess.txt', expect_string=r'#')

    show_dir = net_connect.send_command('dir | inc .bin').split('\n')
    #loop through all files on flash and delete all files that are not the new ios file
    for line in show_dir:
        if filename not in line.split()[-1]:
            print(f"deleteing {line.split()[-1]}")
            net_connect.send_command('delete /force flash:' + line.split()[-1], expect_string=r'#')


def configUpdate():
    pass


#function that disconnects from device
def disconnect(net_connect):
    print('Disconnecting from device...')
    net_connect.disconnect()



#main function that runs the upgrade process
def iosUpgrade():
    #connect to device
    net_connect = connectToDevice(ipaddress, username, password)
    #check if upgrade is required
    upgradeStatus, hardwareType = CheckIfUpgradeIsRequired(net_connect)
    if upgradeStatus == True:
        #set correct ios file nafor device
        iosFile = software_mappings[hardwareType]['software_image']
        #check if file exists on flash
        doseFileExist = checkFileExists(net_connect,iosFile)
        if doseFileExist == False:
            #check if there is enough disk space
            diskCheck = CheckDiskSpace(net_connect)
            if diskCheck == True:
                #copy image to flash
                copyFileToFlash(net_connect,iosFile)
                #update doseFileExist variable
                doseFileExist = checkFileExists(net_connect,iosFile) 
            if diskCheck == False:
                print("Not enough disk space, clean up flash and try again")
                return
        if doseFileExist == True:
            #verify md5 checksum
            checksum = verifyDstImageMd5(net_connect,iosFile,hardwareType)
            if doStagingOnly == True:
                print("Staging complete")
                disconnect(net_connect) 
                return
            #set install method
            set_install_method = software_mappings[hardwareType]['installMethod']
            if checksum == True and set_install_method == 'method1':
                #install image
                installMethod1(net_connect,iosFile)
            if checksum == True and set_install_method == 'method2':
                installMethod2(net_connect,iosFile)
            #wait for 15 seconds
            time.sleep(15)
            #check if device is online
            pingtest=False
            pingtest = pingDevice(ipaddress)
            if pingtest == True:
                #connect to device
                net_connect = connectToDevice(ipaddress, username, password)
                #check if upgradeInProcess.txt is on flash
                upgradeInProcess = checkFileExists(net_connect,'upgradeInProcess.txt')	
                if upgradeInProcess == True and set_install_method == 'method1':
                    #run clean up
                    cleanUpMethod1(net_connect)	
                if upgradeInProcess == True and set_install_method == 'method2':
                    cleanUpMethod2(net_connect,iosFile)	
                    #disconnect from device
                disconnect(net_connect)    


#############################################################################################################
#run this script from for a single device
ipaddress = input("Enter device ip address: ")
username = input("Enter device username: ")
password = getpass("Enter device password: ")
#run ios upgrade
iosUpgrade()

#############################################################################################################
#read a excel file with a list of devices and run the script for each device
#import pandas as pd
#username = input("Enter device username: ")
#password = getpass("Enter device password: ")
#user_device_inout = input("Which device do you want to upgrade ios on: ")
#
#path = 'C:\\Users\\MrRight\\Documents\\GitHub\\HandyPythonScript\\Cisco ios upgrade\\'
#df = pd.read_excel(path+'deviceList.xlsx')
#for index, row in df.iterrows():
#    if  user_device_inout in row['deviceName']: 
#        ipaddress = row['ipaddress']
#        deviceName = row['deviceName']
#        print(f'Upgrading ios on {deviceName} with ip address {ipaddress}')
#        #run ios upgrade
#        iosUpgrade()


#############################################################################################################
#read all txt in a folder and  the script to ios upgrade for each ip address in the txt filename
#import glob
#username = input("Enter device username: ")
#password = getpass("Enter device password: ")
#path = 'C:\\Users\\MrRight\\Documents\\GitHub\\HandyPythonScript\\Cisco ios upgrade\\'
#
#print("Waiting for new txt file (<serial>-<ipaddress>.txt) to be added to folder...")
#print("press ctrl+c to exit")
#try:
#    while True:
#        for fileFound in glob.glob(os.path.join(path, '*.txt')):
#            if "proccessed" not in fileFound:
#                ipaddress = fileFound.split('\\')[-1].split('-')[1].split('.t')[0]
#                filename = fileFound.split('\\')[-1]
#                print(f'File {filename} found')
#                print(f'Upgrading ios on {ipaddress}')
#                #iosUpgrade()
#                #rename file to .proccessed.txt
#                print(f'Renaming {fileFound} to {fileFound}-proccessed.txt')
#                os.rename(fileFound, fileFound + "-proccessed.txt")
#        #wait 20 seconds
#        time.sleep(20)
#except KeyboardInterrupt:
#    pass




