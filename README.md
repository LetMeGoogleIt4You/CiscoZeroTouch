# Cisco Zero Touch Provisioning

This repository does not describe my sex life but how we can deploy Cisco devices with ZTP.

The goal is to load the correct configuration and suitable iOS onto the device fresh from the box.

There are two methods available, one push-based and the other pull-based.

With the pull-based, the new device load the base configuration and it downloads the correct IOS and device-specific configuration. 
With the pushed-based, The new device loads a base configuration, and the deploy server connects to the new device and pushes IOS and device-specific design to the device. 



There is a DHCP server that will point to base confiration file. 
we will also need a file server for the  base confiration, device-specific configuration file and IOS images. 



For more information on how ZTP works look at these links: 
https://github.com/jeremycohoe/IOSXE-Zero-Touch-Provisioning 
https://developer.cisco.com/docs/ios-xe/#!zero-touch-provisioning/ztp-with-tftp-server-running-on-ubuntu-vm

