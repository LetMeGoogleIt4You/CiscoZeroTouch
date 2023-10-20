# Pull-based ZeroTuch
our goal is to load the right configuration and right ios on our new devices without human intervention. 


This guild describe how we can do with zeroTuch with pull-based metoh. 

our topolegies look like this:

            (R1)
             |
           (sw1)
          /    \
(filserver)   (new switchess)


We have DHCP server in the network. In our network the DHCP server will be placed in on the router.
the DHCP server will point all new devices to the conntact the fileserver for a base configuration. 

The file server is connected to the same network as the router and the new devices. 

when a new switch boot it will download the base configuration. This base configuration is configured  so that it will download the device specific configuration and download the right for the deivce.

The device in install the right ios 




R1 configuration:


nnterface gi1
ip add 10.1.1.1 255.255.255.0
no shutdown

ip dhcp pool  ztp_device_pool 
 network 10.1.1.0 255.255.255.0                      
 default-router 10.1.1.1                       
 option 150 ip 10.1.1.1                      
 option 67 ascii /sample_python_dir/python_script.py 
