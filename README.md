# Zero Touch 
This repository does not describe my sex life 
jokes aside this repository dedicated to deploying network devices using Zero Touch Provisioning (ZTP). Our objective is to seamlessly load the appropriate configuration and the correct iOS onto Cisco devices right out of the box.

ZTP enables two primary deployment methods: pull-based and push-based.

## Pull-Based Method
In the pull-based approach, the new device retrieves the `ztp.py` script. This script is responsible for downloading the correct iOS and a device-specific configuration.

## Push-Based Method
With the push-based method, the new device also loads a `ztp.py` script. This script activates SSH on the device and creates a text file on a file server. A separate Python script monitors this file server. When it detects a new file, it establishes a connection to the respective device to download the appropriate iOS and device-specific configuration.


## Environment Setup
Both methods utilize a similar environment setup:
- **DHCP Server:** Configured to point to the base configuration file.
- **File Server:** Stores the base configuration, device-specific configuration files, and iOS images.

Click this [link](https://github.com/LetMeGoogleIt4You/CiscoZeroTouch/blob/main/Environment%20Setup/README.md) to see the environment setup

## Understanding ZTP: A Brief Overview
Zero-Touch Provisioning (ZTP) is part of a suite of zero-day deployment protocols, which includes Plug-and-Play (PnP), Preboot Execution Environment (PxE), and various manufacturer-specific "call home" functions. PnP, PxE and ZTP protocols  leverage DHCP options to facilitate the deployment process. 
We have selected ZTP for its efficiency and broad compatibility.

## ZTP in Action: 
Here's a simplified representation of the ZTP process for a typical Cisco device:

![Diagram](https://github.com/LetMeGoogleIt4You/CiscoZeroTouch/blob/main/Picure/Cisco%20XE%20boot%20modes.png)

**Note:** It's essential to recognize that Cisco models vary significantly; not all devices will adhere to this process identically. Expect variations based on specific model types and configurations.

## Additional Resources
For more detailed information on ZTP, please refer to the following resources:
- [IOSXE Zero Touch Provisioning by Jeremy Cohoe](https://github.com/jeremycohoe/IOSXE-Zero-Touch-Provisioning)
- [ZTP with TFTP Server Running on Ubuntu VM - Cisco Developer](https://developer.cisco.com/docs/ios-xe/#!zero-touch-provisioning/ztp-with-tftp-server-running-on-ubuntu-vm)
- [Day Zero Provisioning Quick Start Guide - Cisco Developer](https://developer.cisco.com/docs/ios-xe/#!day-zero-provisioning-quick-start-guide)


