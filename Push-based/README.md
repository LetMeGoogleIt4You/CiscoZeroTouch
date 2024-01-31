# Push-based Zero-Touch Provisioning

## Objective:
The push-based `ztp.py` will just make the new device ready for an SSH connection and upload a text file to the file server. 

A Python script will be monitoring this folder and will connect to the device using SSH to finish the job by installing new IOS, cleaning up, and installing the device-specific configuration.


## Overviwer of the script


![Push-based-flow](https://github.com/LetMeGoogleIt4You/CiscoZeroTouch/blob/main/Picure/push-based%20ztp.py.png)
