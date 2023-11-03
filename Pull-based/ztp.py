# Importing cli module
from cli import configure, cli, configurep, executep
import re
import time
import urllib
import sys
import logging
import os
from logging.handlers import RotatingFileHandler
import subprocess 

software_mappings = {
    'C9300-24P': {
        'software_image': 'cat9k_iosxe.17.06.05.SPA.bin',
        'software_version': '17.09.04a',
        'software_md5_checksum': '0af35c3ae22f514e92e223f6a0a257f0'
    },
    'C9500-24Q': {
        'software_image': 'cat9k_iosxe.17.06.01.SPA.bin',
        'software_version': '17.06.01',
        'software_md5_checksum': 'fdb9c92bae37f9130d0ee6761afe2919'
    },
    'ASR1001-HX': {
        'software_image': 'asr1000-universalk9.17.05.01a.SPA.bin',
        'software_version': '17.05.01a',
        'software_md5_checksum': '0e4b1fc1448f8ee289634a41f75dc215'
    },
    'C8000V': {
        'software_image': 'cat9k_iosxe.17.09.04a.SPA.bin',
        'software_version': '17.09.04a',
        'software_md5_checksum': '16a20aa19ec9deb2abe421efddb75fae'
    }
}

http_server = '192.168.131.10'
log_to_file = True
do_ios_upgrade = True
do_config_update = True

def main():
    try:
        print ('###### STARTING ZTP SCRIPT ######\n')
        #Creating a log file log_to_file = True
        if(log_to_file == True):
            loggpath = create_file('ztp.log')
            configure_logger(loggpath)
        
        #Find the hardware model
        log_info('- Determining Device Model \n')
        model = get_model()
        log_info('- The device model is %s  \n' % model)
        
        #Checking if hardware is supported by this script
        if model not in software_mappings:
            log_info('- Model %s is not supported by this script ' % model)
            raise ValueError('- Unsupported model')

        #setting variables for software image, version and md5 checksum
        software_image = software_mappings[model]['software_image']
        software_version = software_mappings[model]['software_version']
        software_md5_checksum = software_mappings[model]['software_md5_checksum']

        #Check to see if this IOS is already up to date
        log_info('- Checking if upgrade is required \n')
        update_status, current_version = upgrade_required(software_version)
        #if update_status = true and do_ios_upgrade == True then upgrade is required
        if update_status == True and do_ios_upgrade == True:
            log_info('- Upgrade is required \n')
            #upgradeInProcess.txt on flash for tracking
            log_info('- Creating is upgradeInProcess.txt file on flash:guest-share/ \n')
            create_file('upgradeInProcess.txt')
            #Check if image transfer needed, 
            log_info('- Checking to see if %s exists on %s \n' % (software_version, "flash:/"))
            file_status = check_file_exists(software_image)
            #If Check_file_exists == False transfer the IOS image
            if file_status == False:
                log_info('- %s Missing attempting to download image to switch... \n' % (software_version))
                file_transfer(http_server, software_image)
                #Take a new file status after the transfer
                file_status = check_file_exists(software_image)
            
            #If Check_file_exists == Ture move on to md5 check
            if file_status == True:
                log_info('- Attempting md5 hash... \n')
                md5_status = verify_dst_image_md5(software_image, software_md5_checksum)
                if  md5_status == False:
                  log_info('- Md5 check fail Attempting to retransfer image to device... \n')
                  file_transfer(http_server, software_image)
                  log_info('- Md5 check fail after  retransfer image to device... \n')
                  md5_status = verify_dst_image_md5(software_image, software_md5_checksum)
            
            if file_status == True and md5_status == True:
                log_info('- Deploying EEM upgrade script \n')
                deploy_eem_sw_upgrade_script(software_image)
                log_info('- Performing the upgrade - switch will reboot ***\n')
                cli('event manager run upgrade')
                time.sleep(600) #sleep for 600 seconds
                log_info('- EEM upgrade took more than 600 seconds to reload the device..Increase the sleep time by few minutes before retrying \n')
        else:
          log_info('- Upgrade is not required \n')
        
        #Check if cleanup is necessary
        log_info('- Check if cleanup is necessary \n')
        # Cleanup any leftover install files, if upgradeInProcess.txt exist on flash then run the cleanup eem script
        check_upgradeInProcess_file = check_file_exists('guest-share/upgradeInProcess.txt')	
        if check_upgradeInProcess_file == True:
            log_info('- Deploying Cleanup EEM Script \n')
            deploy_eem_sw_cleanup_script()
            log_info('- Running Cleanup EEM Script \n')
            cli('event manager run cleanup')
            time.sleep(40) #sleep for 40 seconds
            log_info('- Deleting upgradeInProcess.txt file \n')
            cli('delete /force flash:guest-share/upgradeInProcess.txt')
            check_upgradeInProcess_file = check_file_exists('guest-share/upgradeInProcess.txt')
        if check_upgradeInProcess_file == False:
            log_info('- Cleanup is not necessary \n')
        
        #Check if config update is needed
        if do_config_update == True:
            log_info('- starting config update \n')
            #Find the serial number
            log_info('- Determining Device Serial Number \n')
            serial = get_serial()
            log_info('- The device serial number is %s  \n' % serial)

            #print config file name to download
            config_file = '%s-config.cfg' % serial
            log_info('- Trying to downloading config file %s-config.cfg \n' % serial)
            file_downaload = file_transfer(http_server, config_file)
            if file_downaload == False:
                log_info('- Was unable to download config file \n')
                raise ValueError('- Was unable to download config file')
            if file_downaload == True:
                log_info('- Config file downloaded \n')
                #update the config file
                log_info('- Merging configuration \n')
                configure_merge(config_file)
                log_info('- Configuration merged \n')

                #making crypto rsa key
                log_info('- Making crypto rsa key \n')
                configure('crypto key generate rsa modulus 4096')
                log_info('- Crypto rsa key made \n')

                #save config
                log_info('- saving configuration \n')
                configure('do write memory')
                log_info('- Configuration saved \n')
        log_info('######  END OF ZTP SCRIPT ######\n')
    
    except Exception as e:
        log_critical('- Failure encountered during day 0 provisioning . Aborting ZTP script execution. Error details below \n' + e)
        print(e)
        sys.exit(e)

#function that configures logger      
def configure_logger(path):
    log_formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
    logFile = path
    #create a new file > 5 mb size
    log_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024, backupCount=10, encoding=None, delay=0)
    log_handler.setFormatter(log_formatter)
    log_handler.setLevel(logging.INFO)
    ztp_log = logging.getLogger('root')
    ztp_log.setLevel(logging.INFO)
    ztp_log.addHandler(log_handler)

#function that logs info messages
def log_info(message):
    print (message)
    if(log_to_file == True):
        ztp_log = logging.getLogger('root')
        ztp_log.info(message)

#function that logs critical messages
def log_critical(message ):
    print (message)
    if(log_to_file == True):
        ztp_log = logging.getLogger('root')
        ztp_log.critical(message)

#function that creates a file
def create_file(filename):
    try:
        print ("- Creating a log file \n ")
        path = '/flash/guest-share/' + filename
        with open(path, 'a+') as fp:
             pass
        print ("- %s file created \n " %filename)
        return path
    except IOError:
      print("- Couldn't create a log file at guset-share .Trying to use  /flash/%s as an alternate log path\n"  %filename)
      path = '/flash/'+ filename
      with open(path, 'a+') as fp:
             pass
      print ("- %s file created \n "  %filename)
      return path
    except Exception as e:
         print("- Couldn't create a %s file to proceed" %filename)

#function that gets model of the device
def get_model():
    command = 'show version | inc cisco.*memory '
    try:
        show_version = cli(command)
    except Exception as e:
        time.sleep(90)
        show_version = cli(command)
    model = show_version.split()[1]
    #print(model)
    return model

#function that checks if upgrade is required
def upgrade_required(target_version):
    # Obtains show version output
    show_version = cli('show ver | inc re, Version')
    current_version = show_version.split()[-1]
    log_info('- Current Code Version is %s  \n' % current_version)
    log_info('- Target Code Version is %s  \n' % target_version)
    # Returns False if on approved version or True if upgrade is required
    if (target_version == current_version):
        return False, current_version
    else:
        return True, current_version


#function that checks if file exists on flash
def check_file_exists(file, file_system='flash:/'):
    results = cli('dir ' + file_system + file)
    if 'No such file or directory' in results:
        log_info('- The %s does NOT exist on %s \n' % (file, file_system))
        return False
    elif 'Directory of %s%s' % (file_system, file) in results:
        log_info('- The %s DOES exist on %s \n' % (file, file_system))
        return True
    elif 'Directory of %s%s' % ('bootflash:/', file) in results:
        log_info('- The %s DOES exist on %s \n' % (file, 'bootflash:/'))
        return True
    else:
        log_critical('- Unexpected output from check_file_exists \n')
        raise ValueError("Unexpected output from check_file_exists")
         
#function that transfers file from http server to flash
def file_transfer(http_server, file):
  log_info('- Start transferring from http://%s/%s to flash:%s  \n' % (http_server,file,file))
  try:
    results = cli('copy http://%s/%s flash:%s \n' % (http_server,file,file))
    print(results)
    if 'Error opening http://' in results:
        log_critical('- Failed to transfer file, make sure the file on the server \n')
        raise ValueError("Failed to transfer file, make sure the file on the server")
    elif 'Invalid input detected' in results:
        log_critical('- Failed to transfer, Invalid input detected \n')
        raise ValueError("Failed to transfer, Invalid input detected")
    elif 'Invalid URL' in results:
        log_critical('- Failed to transfer file, Invalid URL \n')
        raise ValueError("Failed to transfer file, Invalid URL")
    elif 'copied' in results:
        log_info('- Finished transferring file \n')
        return True
  except Exception as e:
    log_critical('- Failed to transfer file \n')
    log_critical('copy http://%s/%s flash:%s  command failed \n' % (http_server,file,file ))
    log_critical(e) 
    return False


#function that verifies md5 checksum of the image
def verify_dst_image_md5(image, src_md5, file_system='flash:/'):
    verify_md5 = 'verify /md5 ' + file_system + image
    try:
        dst_md5 = cli(verify_md5)
        if src_md5 in dst_md5:
           log_info('- MD5 hashes match \n')
           return True
        else:
          log_info('- MD5 checksum mismatch \n')
          return False
    except Exception as e:
       print(e)
       log_info('-  MD5 checksum failed due to an exception \n')
       log_info(e)
       return True

#function that deploys upgrade eem script
def deploy_eem_sw_upgrade_script(image):
    install_command = 'install add file flash:/' + image + ' activate commit'
    eem_commands = ['event manager applet upgrade',
                    'event none maxrun 600',
                    'action 1.0 cli command "enable"',
                    'action 2.0 cli command "%s" pattern "\[y\/n\/q\]"' % install_command,
                    'action 2.1 cli command "n" pattern "proceed"',
                    'action 2.2 cli command "y"'
                    ]
    results = configurep(eem_commands)
    log_info('- Successfully configured upgrade EEM script on device')

#function that deploys cleanup eem script
def deploy_eem_sw_cleanup_script():
    install_command = 'install remove inactive'
    eem_commands = ['event manager applet cleanup',
                    'event none maxrun 600',
                    'action 1.0 cli command "enable"',
                    'action 2.0 cli command "%s" pattern "\[y\/n\]"' % install_command,
                    'action 2.1 cli command "y" pattern "proceed"',
                    'action 2.2 cli command "y"'
                    ]
    results = configurep(eem_commands)
    log_info('- Successfully configured cleanup EEM script on device \n')

#function that gets serial number of the device
def get_serial():
    try:
        show_version = cli('show version')
    except Exception as e:
        time.sleep(90)
        show_version = cli('show version')
    try:
        serial = re.search(r"System Serial Number\s+:\s+(\S+)", show_version).group(1)
    except AttributeError:
        serial = re.search(r"Processor board ID\s+(\S+)", show_version).group(1)
    return serial


#function that updates running config with config file
def update_config(file,file_system='flash:/'):
    update_running_config = 'copy %s%s running-config' % (file_system, file)
    save_to_startup = 'write memory'
    log_info("- Copying to startup-config \n")
    running_config = executep(update_running_config)
    startup_config = executep(save_to_startup)

 
#function that replaces running config with config file
def configure_replace(file,file_system='flash:/' ):
        config_command = 'configure replace %s%s force' % (file_system, file)
        log_info('- Replacing configuration \n')
        config_repl = executep(config_command)
        time.sleep(30) #sleep for 30 seconds


#function that merges config file with running config
def configure_merge(file,file_system='flash:/'):
     log_info('- Merging running config with given config file \n')
     config_command = 'copy %s%s running-config' %(file_system,file)
     config_repl = executep(config_command)
     time.sleep(30) #sleep for 30 seconds



if __name__ == "__main__":
    main()
