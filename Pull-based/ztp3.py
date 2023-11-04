
# Importing cli module
import cli
import re
import time
import urllib
import sys
import logging
import os
from logging.handlers import RotatingFileHandler
import subprocess 


#function that transfers file from http server to flash
def file_transfer1(http_server, file):
  command1 = ('ping %s' % (http_server))
  res = cli.execute(command1)
  print(res)
  time.sleep(30)
  print('- Start transferring  file \n')
  command2 = 'copy tftp:%s/%s flash:/%s ' % (http_server,file,file)
  print(command2)
  res = cli.execute(command2)
  print(res)
  print("\n")
  print('- Finished transferring device configuration file\n')


def file_transfer2(http_server, file):
    results = cli.configure('file prompt quiet')
    eem_commands = ['event manager applet download',
                    'event none maxrun 900',
                    'action 1.0 cli command "enable"',
                    'action 2.0 cli command "copy http://%s/%s flash:/%s" ' % (http_server,file,file),
                    'action 2.1 cli command "" pattern "Destination"',
                    'action 2.2 cli command ""'
                    ]
    results = cli.configurep(eem_commands)
    print('- Successfully configured download EEM script on device \n')



#file_transfer1('192.168.131.10', 'cat9k_iosxe.17.06.05.SPA.bin')

file_transfer2('192.168.131.10', 'cat9k_iosxe.17.06.05.SPA.bin')
cli.execute('event manager run download')
time.sleep(600) #sleep for 600 seconds

#copy tftp://192.168.131.10/cat9k_iosxe.17.06.05.SPA.bin flash:/cat9k_iosxe.17.06.05.SPA.bin