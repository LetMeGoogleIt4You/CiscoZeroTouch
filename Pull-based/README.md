# Pull-based ZeroTuch
Our goal is to load the right configuration and right ios on our new devices without human intervention. 

This guild describe how we can do with zeroTuch with pull-based metoh. pull-based metoh meaning the new switch fixes is going all the work witkout any addtion software monetoring the process.

The topolegies look like this:

               (R1)
                |
              (sw1)
             /     \
            /       \
(ZeroTouchServer)   (new switches)


We have DHCP server in the network. We can use R1 as DHCP server or install a DHCP on the ZeroTouchServer.
the DHCP server will point all new devices to the conntact the fileserver for a base configuration. 

The file server(in our case we use http server) is connected to the same network as the router and the new devices. 

When a new switch boot it will download the base configuration. This base configuration is configured  so that it will download the device specific configuration and download the right for the deivce.

The device in install the right ios, right config




## Setting up the enviroment
We need to set opp a DHCP server and HTTP server. 
the new swiches must have reachabilety to the HTTP server and in out case we put them in the same vlan. 


### Setting up a HTTP server

We wil be using ubuntu server and installed apache2 to act as our file server. 
the ubuntu server should have a static, we will be using  192.168.131.10 for the server

1) sett up the ubuntu server


2) Install the apache2
sudo apt update
sudo apt install apache2
sudo ufw allow 'Apache'
sudo systemctl status apache2

3) Copy files to 
copy the base configuration file(ztp.py), nessesry confiration and ios to the nessesry 
use the following naming convertion for the config file 
<deivce serial nummer>-configuration.txt

4) test
test the file copy from a device


### Setting up a DHCP server alternativ 1
we can use R1 as DHCP server and point option 150 to http server, and option to the file


ip dhcp excluded-address 192.168.131.0 192.168.131.50
ip dhcp pool ztp_device_pool 
 network 192.168.131.0 255.255.255.0                      
 default-router 192.168.131.1                       
 option 150 ip 192.168.131.10                     
 option 67 ascii /python_script.py 

### Setting up a  DHCP server alternativ 2

we can also instal a DHCP server on the ubuntu server


