# Pull-based Zero-Touch Provisioning

Objective:
The primary aim is to automate the loading of the correct iOS and configuration onto our new devices, eliminating the need for manual intervention.


Guide Overview:
This guide provides a detailed approach to implementing Zero-Touch Provisioning using a pull-based method. In a pull-based model, the new switch undertakes the necessary actions independently, without the need for additional software to monitor the process.


Topology Overview:
Below is a representation of the network topology utilized in this approach:


```
               (R1)
                |
              (sw1)
             /     \
            /       \
(ZeroTouchServer)   (new switches)
```

Network Components:
- **DHCP Server**: A DHCP server is essential in our network for directing new devices to retrieve their base configurations from a file server.
  - It can be set up using an existing router (like R1) or by installing one on the ZeroTouchServer.
- **File Server**: In our setup, we use an HTTP server that hosts the base configuration files.
  - The HTTP server and the new devices are on the same network, simplifying the retrieval process.

Device Boot-up Process:
Upon booting, a new switch will:
1. Contact the DHCP server to obtain an IP address and the location of the file server.
2. The switch will reach out to the file server to download its base configuration(ztp.py).
3. The switch will exicute the ztp.py inside a guestshell that are automatically deployed by the switch 


Environment Setup:
To support the pull-based Zero-Touch Provisioning process, a DHCP server and an Fileserver server are required. The new switches should have accebilety to the http sercer within the same VLAN for ease of communication.

### Setting Up an HTTP Server (acting as a file server)
We will be using an Ubuntu server with Apache2 as our file server.

#### 1) Configure Ubuntu Server with a Static IP
First, we need to assign a static IP to our Ubuntu server, for example, `192.168.131.10`.

```bash
ip a
cd /etc/netplan
ls
cat 00-network-manager-all.yaml
cp 00-network-manager-all.yaml backup-network-manager-all.yaml
vim 00-network-manager-all.yaml
```


Change the 00-network-manager-all.yaml to set a static ip


```
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
  version: 2
```

applying the network settings

```
sudo netplan apply
```



2) Install the apache2

```
sudo apt update
sudo apt install apache2
sudo ufw allow 'Apache'
sudo systemctl status apache2
```


3) Copy files to server
Copy the base configuration file(ztp.py), the confiration files and ios to the this location /var/www/html  on the ubuntu server

Use the following naming convertion for the config file 
<deivce serial nummer>-configuration.txt

4) Test the file copy from a device
We can test file transer by connection 

### Setting up a DHCP server alternativ 1
we can use R1 as DHCP server and point option 150 to http server, and option to the file


```
ip dhcp excluded-address 192.168.131.0 192.168.131.50
ip dhcp pool ztp_device_pool 
 network 192.168.131.0 255.255.255.0                      
 default-router 192.168.131.1                                      
 option 67 ascii http://192.168.131.10/ztp.py
```

### Setting up a  DHCP server alternativ 2

we can also instal a DHCP server on the ubuntu server

```
sudo apt install isc-dhcp-server
sudo systemctl status isc-dhcp-server
sudo vim /etc/dhcp/dhcpd.conf
```

Add the following lines to the dhcpd.conf and modify the the subnet to your local enviroment:


```
option domain-name "localhost.localdomain";
default-lease-time 600;
max-lease-time 7200;
ddns-update-style none;
#option ip-tftp-server code 150 = { ip-address };
authoritative;
# DHCP range for ZTP on C9300
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