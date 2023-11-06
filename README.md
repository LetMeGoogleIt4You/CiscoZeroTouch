# Cisco Zero Touch

This repository does not describe my sex life but how we can deploy Cisco devices with ZeroTouch.

The goal is to load the correct configuration and suitable iOS onto the device fresh from the box.

There are two methods available, one push-based and the other pull-based.

With the pushed-based, The new device loads a default configuration, and the deploy server connects to the device and pushes IOS and device-specific design to the device. 
With the pull-based, the new device does all the work; it downloads the correct IOS and device-specific configuration. 


There is a DHCP server to load the default configuration
There is also a service with the device-specific configuration and IOS files. 

