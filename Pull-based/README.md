# Pull-based Zero-Touch Provisioning

## Objective:
The primary aim is to automate the loading of the correct Cisco IOS and configuration onto our new devices, eliminating the need for manual intervention.


## Guide Overview:
This guide provides a detailed approach to implementing Zero-Touch Provisioning using a pull-based method. In a pull-based model, the new device undertakes the necessary actions independently, without the need for additional software to monitor the process.


## Topology Overview:
Below is a representation of the network topology utilized in this guide:


```
               (R1)
                |
              (sw1)
             /     \
            /       \
(ZeroTouchServer)   (new device)
```

## Network Components:
- **DHCP Server**: A DHCP server is essential in our network for directing new devices to retrieve their base configurations (`ztp.py`) from a file server.
  - It can be set up using an existing router (like R1) or by installing a DHCP server on the ZeroTouchServer.
- **File Server**: In this guide, we use an HTTP server but TFTP server is also supported to act as a file server that hosts the base configuration files (`ztp.py`), IOS, and device-specific configuration.
  - The new devices should have reachability to the file server.


## Device Boot-up Process:
Upon booting, a new device will:
1. The new device will contact the DHCP server to obtain an IP address and the location of the file server.
2. The device will reach out to the file server to download its base configuration(`ztp.py`).
3. The device will exicute the ztp.py inside a guestshell that are automatically deployed by the device 


# Environment Setup:
To support the pull-based Zero-Touch Provisioning process, a DHCP server and an Fileserver server are required. The new devices should have accebilety to the http sercer within the same VLAN for ease of communication. All devices should support ZTP.

### Setting Up an HTTP Server to acting as a file server
We will be using an Ubuntu server with Apache2 as our file server.

1) Configure Ubuntu Server with a Static IP
First, we need to assign a static IP to our Ubuntu server, for example, `192.168.131.10`.

```bash
ip a
sudo ls /etc/netplan/
sudo cat /etc/netplan/00-network-manager-all.yaml
sudo cp /etc/netplan/00-network-manager-all.yaml /etc/netplan/backup-network-manager-all.yaml
sudo vim /etc/netplan/00-network-manager-all.yaml
```


Change the 00-network-manager-all.yaml to set a static ip


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

Apply the new network settings and verify the static ip address:


```bash
sudo netplan apply
ip a
```


2) Install Apache2

```bash
sudo apt update
sudo apt install apache2
sudo ufw allow 'Apache'
sudo systemctl status apache2
```


3) Copy Configuration and iOS Files to Server
The base configuration file (ztp.py), device-specific configuration files, and iOS should be placed in the /var/www/html directory on the Ubuntu server.
Use a naming convention like <device_serial_number>-config.cfg for the config files.

4) Testing File Transfer
To ensure the files server is working, perform a test transfer from a one of devices.

```
copy http://192.168.131.10/somefile flash:
```


### Setting Up a DHCP Server (Option 1)
Utilize R1 as a DHCP server, configuring it to point to the HTTP server for option 150, and defining the bootfile for new devices.


```
ip dhcp excluded-address 192.168.131.0 192.168.131.50
ip dhcp pool ztp_device_pool 
 network 192.168.131.0 255.255.255.0                      
 default-router 192.168.131.1                                      
 option 67 ascii http://192.168.131.10/ztp.py
```

### Setting Up a DHCP Server (Option 2)

we can also install a DHCP server on the ubuntu server

```bash
sudo apt install isc-dhcp-server
sudo systemctl status isc-dhcp-server
sudo vim /etc/dhcp/dhcpd.conf
```

Modify dhcpd.conf to fit the local environment and add the following configuration:


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
	option bootfile-name "http:/192.168.131.10/ztp-simple.py";
}
```

Make sure to replace http://192.168.131.10/ztp-simple.py with the our path to your Zero-Touch Provisioning script.

### Make necessary changes to ztp.py if needed

You may need to make changes to (`ztp.py`) if your environment is different

For troubleshooting the (`ztp.py`) script you can  bring up the guestshell manually

Enable guestshell

```conf
conf t
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

Log into guestshell make a ztp.py file and run it

```conf
guestshell
[guestshell@guestshell ~]$vi ztp.py
[guestshell@guestshell ~]$ python3 ztp.py 
```


If you need to totaly delete a device use this script by this hero https://pastebin.com/JcEydZ33 

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