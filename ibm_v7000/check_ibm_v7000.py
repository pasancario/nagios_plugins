
#!/usr/bin/env python
# vim: set ts=2 sw=2 sts=2 expandtab:
#
# Author: Luis I. Perez Villota <chewieip@gmail.com>
# License: GPL-2
#
# Changelog:
# 2015-07-23: First version
# 
# Description:
# 
# check_ibm_v7000 Allows you to check Storage Status of IBM V7000. 
# Is using ssh command to allow connection
# First version works with password configuration passed by parameters. 
# TODO: 
# Using public keys
# 
# Works as a nagios plugin based on online/offline devices in V7000
#

from pprint import pprint 
import paramiko
import sys
import socket
import re

from optparse import OptionParser

RC_OK = 0
RC_CRIT = 2

command_patterns = {'lsarray' : {
                                 'Pattern' : '%s : %s ',
                                 'values' : [1,4],
                                 'Message' : "Array(s) ",
                                 'OK_Message' : "All Arrays in proper State",
                                 },
                    'lsdrive' : {
                                 'Pattern' : 'Enclosure_ID : %s Slot ID: %s  ',
                                 'values' : [-2,-1],    
                                 'Message' : "Drive(s) ",                      
                                 'OK_Message' : "All Drives in proper State",       
                                 },
                    'lsvdisk' : {
                                 'Pattern' : 'name : %s Disk Group: %s  ',
                                 'values' : [1,6],    
                                 'Message' : "Disk(s) ",  
                                'OK_Message' : "All Disks in proper State",                          
                                 },
                    'lsenclosure' : {
                                 'Pattern' : 'ID : %s Serial Number: %s  ',
                                 'values' : [0,7],    
                                 'Message' : "Enclosure(s) ",  
                                'OK_Message' : "All Enclosure Modules in proper State",                          
                                 },
                    }
def execute_command(ip,user,password,command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())    
    try:
        ssh.connect(ip, username=user, password=password, port=22, allow_agent=False,look_for_keys=False, timeout=5)
        stdin, stdout, stderr = ssh.exec_command(command)
        results = stdout.readlines()
    except socket.timeout:
        print "Error: Socket Timeout connecting to Server %s " % ip
        sys.exit(RC_CRIT)    
    except paramiko.ssh_exception.AuthenticationException as error:
        print "Error: %s . Check your user/password " % error
        sys.exit(RC_CRIT)

    return results

def lsanalyze(results,command):
    crit_disk = []
    PATTERN = 'offline'
    for line in results:
        new_line = re.sub( '\s+', ' ', line ).strip()
        if  PATTERN in new_line:
            arr_line = new_line.split(' ')
            disk_offline = command_patterns[command]['Pattern']  % (new_line.split(' ')[command_patterns[command]['values'][0]],new_line.split(' ')[command_patterns[command]['values'][1]])
            crit_disk.append(disk_offline)
    
    if len(crit_disk)>0:
        message = "ERROR : %s %s " % (command_patterns[command]['Message'],' OFFLINE, '.join(crit_disk))
        rc = RC_CRIT
    else:
        message = command_patterns[command]['OK_Message']
        rc = RC_OK
    return rc,message

               
                
def analyze(query,results):    
    if query in('lsarray','lsdrive','lsvdisk','lsenclosure'):        
        rc,message = lsanalyze(results,query)
    else:
        pprint(results)
        rc = 0
        message = "Testing"
    return rc,message 


COMMANDS_LIST = ['lsarray','lsdrive','lsvdisk','lsenclosure',
                 'lsenclosurebattery','lsenclosurecanister',
                 'lsenclosurepsu','lsenclosureslot',
                 'lsrcrelationship','unified']
                            
if __name__ == '__main__':   
    parser = OptionParser()
    parser.add_option("-u","--user",
        dest="user",
        help="User with Monitoring privileges" ,
        default = None)
    parser.add_option("-p","--password",
        dest="password",
        help="Password" ,
        default = None)
    parser.add_option("-s","--server",  
        dest="server",
        help="Server" ,
        default = None)    
# First version works with password configuration 
    parser.add_option("-c","--command",
        dest="command",
        help="Command to execute " ,
        default = None)
    (options, args) = parser.parse_args()
    
    
    if options.server is None:
        print "Error: There is no Server "
        sys.exit(RC_CRIT)
    else:
        server = options.server
    if options.user is None:
        user = 'nagios'
    else:
        user = options.user            
    if options.password is None:        
        password = 'nagios'
    else:
        password = options.password        
    if options.command is None:
        print "Error: Commands Accepted: [%s] " % ', '.join(COMMANDS_LIST)
        sys.exit(RC_CRIT)
    elif options.command not in COMMANDS_LIST:
        print "Error: Commands Accepted: [%s] " % ', '.join(COMMANDS_LIST)
        sys.exit(RC_CRIT)
    else:
        command = options.command    
    results = execute_command(server,user,password,command)
    rc, message = analyze(command,results)
    
    print message
    sys.exit(rc)        
    
        