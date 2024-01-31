# Zero-Touch Provisioning (ZTP) Environment Setup Guide

## Objective:
The objective is to set up the environment for Zero-Touch Provisioning (ZTP), enabling new devices to be onboarded automatically.
This guide presents a detailed procedure for setting up a Zero-Touch Provisioning (ZTP) environment.


## Disclaimer
- **Environmental Variations:** The settings and procedures in this guide may need adjustments to fit specific network environments.
- **Hardware Compatibility:** This guide primarily targets Cisco devices; however, some steps may vary for other manufacturers.


## Topology Overview:
The following diagram illustrates the network topology used in this guide:
- R1 is our router; it is not strictly necessary unless you plan to run the DHCP server on the router.
- SW1 is the switch to which all our devices are connected. For simplicity, the ZTP server and all new devices are placed in VLAN 1. This may need to be altered for production environments.
- ZTP server: This serves as our file server. If needed, the DHCP server can also be installed on the ZTP server.

```
               (R1)
                |
              (SW1)
             /     \
            /       \
(ZTP-Server)   (new device)
```

## Network Components:
- **DHCP server**: A DHCP server is essential in our network for directing new devices to retrieve the `ztp.py` file from the  server with option 67.
  - It can be set up using a router (like R1) or by installing a DHCP server on a server.
- **File sharing server**: In this guide, we will demonstrate how to use both HTTP or TFTP protocols to act as a file server. This file server will host the  `ztp.py` files , IOSes, and device-specific configurations.
  - New devices must have reachability to the file server.

## Device Boot-up Process:
Upon booting, a new device will:
1. Contact the DHCP server to obtain an IP address.
2. The DHCP will respond with a DHCP offer with IP address, subnet mask, default gateway and with option 67 with the path to the file server for the device to download its `ztp.py` file.
3. The device will reach out to the file server to download its  `ztp.py`.
4. Then the device will execute the `ztp.py` inside a guest shell that is automatically deployed by the device. When the script is done, the guest shell will destroy itself.

## ZTP file
There are two types of `ztp.py` files in this repository: one pull-based and one push-based.
- With the pull-based `ztp.py` file, the new device does an IOS upgrade, cleans old installation files, and installs the device-specific configuration by itself.
- The push-based `ztp.py` will just make the new device ready for an SSH connection and upload a text file to the file server. A Python script will be monitoring this folder and will connect to the device using SSH to finish the job by installing new IOS, cleaning up, and installing the device-specific configuration.

Choose the pull-based or push-based `ztp.py` file that fits your environment best.

### Setting up a ZTP Server
In this guide, we will be using an Ubuntu server to act as our ZTP server (file server).

After installing the Ubuntu server, it is recommended to configure the server with a static IP.
In this guide, we will be using IP `192.168.131.10`.

```bash
ip a
sudo ls /etc/netplan/
sudo cat /etc/netplan/00-network-manager-all.yaml
sudo cp /etc/netplan/00-network-manager-all.yaml /etc/netplan/backup-network-manager-all.yaml
sudo vim /etc/netplan/00-network-manager-all.yaml
```


Change the 00-network-manager-all.yaml to set a static IP. 


```yaml
network:
  renderer: networkd
  ethernets:
    ens160:
      addresses:
        - 192.168.131.10/24
      nameservers:
        addresses: [1.1.1.1, 1.0.0.1]
      routes:
        - to: default
          via: 192.168.131.1
    ens192:
      dhcp4: yes
  version: 2
```

Apply the new network settings and verify the static IP address:


```bash
sudo netplan apply
ip a
ping 192.168.131.1
```

## Setting up File Sharing Server
We will demonstrate two options for a file server:

* Option 1: Using an HTTP server
* Option 2: Using a TFTP server


### Setting up an HTTP File Sharing Server (Option 1)
We can use Apache2 to act as our HTTP file sharing server.

Install Apache2:

```bash
sudo apt update
sudo apt install apache2
sudo ufw allow 'Apache'
sudo systemctl status apache2
```


### Setting up a TFTP File Sharing Server (Option 2)
We can also use tftpd-hpa to act as our TFTP file sharing server.

Install tftpd-hpa:

```bash
sudo apt update
sudo apt install tftpd-hpa
sudo systemctl status tftpd-hpa
```

Modify the config file:


```bash
sudo vi /etc/default/tftpd-hpa
```

Change any settings if needed:

```
# /etc/default/tftpd-hpa
TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/var/lib/tftpboot"
TFTP_ADDRESS=":69"
TFTP_OPTIONS="--secure --create"
```

Restart the TFTP server:

```bash
sudo systemctl restart tftpd-hpa
```


### Upload the necessary files to the file Server
When the file server is up and running, copy the `ztp.py` file, device-specific configuration files, and IOS to the file server in the right location.

- If you are using Apache2, the default directory is `/var/www/htm`.
- If you are using tftpd-hpa, the default directory is `/var/lib/tftpboot`.

The naming convention for the device-specific configuration is `<serial number>-config.txt`.

### Verify the File Server
When the file server is up and running and files are copied to the correct directory, do a quick verification to ensure it works.
Log in to a working device and make sure the file server is operational.

```
copy http://192.168.131.10/ztp.py flash:ztp.py

or

copy tftp://192.168.131.10/ztp.py flash:ztp.py
```

## Setting up a DHCP Server
We will also cover two options for setting up a DHCP server.
Make sure to use the right transfer protocol. In these examples, we will be using the HTTP protocol to copy the `ztp.py` to the device.
If you are using TFTP as the file transfer protocol, just change it from HTTP to TFTP.

### Setting Up a DHCP Server on a cisco device (Option 1)
We can utilize R1 as a DHCP server, configuring it so that option 67 points to the file server and `ztp.py` file.


```
ip dhcp excluded-address 192.168.131.0 192.168.131.50
ip dhcp pool ztp_device_pool 
 network 192.168.131.0 255.255.255.0                      
 default-router 192.168.131.1                                      
 option 67 ascii http://192.168.131.10/ #if you are using http
```

### Setting Up a DHCP Server on the Ubuntu server (Option 2)
A second option is to install a DHCP server on the Ubuntu server.


```bash
sudo apt install isc-dhcp-server
sudo systemctl status isc-dhcp-server
sudo vim /etc/dhcp/dhcpd.conf
```

Modify dhcpd.conf to fit the local environment:


```conf
option domain-name "localhost.localdomain";
default-lease-time 600;
max-lease-time 7200;
ddns-update-style none;
#option ip-tftp-server code 150 = { ip-address };
authoritative;
# DHCP range for ZTP
subnet 192.168.131.0 netmask 255.255.255.0 {
	range 192.168.131.100 192.168.131.250;
	option domain-name "localhost.localdomain";
	option subnet-mask 255.255.255.0;
	option broadcast-address 192.168.131.255;
	default-lease-time 600;
	max-lease-time 7200;
	option bootfile-name "http:/192.168.131.10/ztp.py";
}
```

Your environment may look different, so make any necessary changes to fit your environment.

### End of environment setup
When the setup of the file server and DHCP server is complete, you are ready to deploy devices using ZTP.


# Tips and tricks for troubelshooting the enviroemnt
In some very rare occasion you may need to troubleshoot the environment. Here are some tips and tricks.

## Verify connectivety
verify that the new device can access the ZTP server

## Test the ztp.py File
We can run the `ztp.py` script manually by enabling guestshell on a device.

To enable guest shell do the following:

```conf
conf t
iox
int virtualportGroup 1
ip add 192.168.1.1 255.255.255.0
no shut
app-hosting appid guestshell
app-vnic gateway0 virtualportgroup 1 guest-interface 0 
guest-ipaddress 192.168.1.2 netmask 255.255.255.0 
app-default-gateway 192.168.1.1 guest-interface 0 
name-server0 1.1.1.1
end
guestshell enable
```

Wait to guestshell is up and running and loggin the gestshell.
Log into guestshell make a ztp.py file and run it.

```conf
guestshell
[guestshell@guestshell ~]$vi ztp.py
copy the code and save the file
[guestshell@guestshell ~]$ python3 ztp.py 
```


## Resett a device
If you need to completely resett a device use this script proviced by this hero https://pastebin.com/JcEydZ33.

```
Conf t
!
alias exec prep4pnp event manager run prep4pnp
!alias exec show-pov-version event manager run show-pov-version
!
event manager applet prep4pnp
event none sync yes
action a1010 syslog msg "Start: 'prep4pnp'  EEM applet."
action a1020 puts "Preparing device to be discovered by device automation.  Note: This script will reboot the device."
!action a1000 wait 360
action b1010 cli command "enable"
action b1020 puts "Stopping pnp for now"
action b1030 cli command "no pnp profile pnp-zero-touch"
action b1040 puts "Saving config to update BOOT param."
action b1040 cli command "write"
action c1010 puts "Erasing startup-config."
action c1020 cli command "write erase" pattern "confirm"
action c1030 cli command "y"
action d1010 puts "Clearing crypto keys."
action d1020 cli command "config t"
action d1030 cli command "crypto key zeroize" pattern "yes/no"
action d1040 cli command "y"
action e1010 puts "Clearing crypto PKIwri         stuff."
action e1020 cli command "no crypto pki cert pool" pattern "yes/no"
action e1030 cli command "y"
action e1040 cli command "exit"
action f1010 puts "Deleting vlan.dat file."
action f1020 cli command "delete /force vlan.dat"
action g1010 puts "Deleting certificate files in NVRAM."
action g1020 cli command "delete /force nvram:*.cer"
action h0001 puts "Deleting PnP files"
action h0010 cli command "delete /force flash:pnp*"
action h0020 cli command "delete /force nvram:pnp*"
action z1010 puts "Device is prepared for being discovered by device automation.  Rebooting."
action z1020 syslog msg "Stop: 'prep4pnp' EEM applet."
action z1030 reload
!
!
End
 
prep4pnp


```



