
#!/usr/bin/env python
# vim: set ts=2 sw=2 sts=2 expandtab:
#
# Author: Luis I. Perez Villota <chewieip@gmail.com>
# License: GPL-2
#
# Changelog:
# 2015-05-05: First version
# 
# Description:
# 
# check_esb_proxy Allows you to check services available in a Proxy-mode Apache Synapse.
# A config file as BASELINE is needed. If not, it will skip configuration. 
# 
# Works as a nagios plugin
#

import os
import sys
import re
from optparse import OptionParser
import urllib2
from HTMLParser import HTMLParser

#PORT DEFAULT for SYNAPSE
PORT_DEFAULT = "8000"
BASE_URL = "http://%s:%d/services"
BASE_CONFIG = "services.cfg"
SERVICES = []
SERVICES_LOCAL = []
(RC_OK, RC_WARN, RC_CRIT, RC_UNKNOWN) = range(0,4)
RC_TXT = ["OK","WARNING", "CRITICAL", "UNKNOWN"]

"""
Helper class for HTMLParser. 
It checks for a webservice in html from services webpage from synaps3e
"""
class MyHTMLParser(HTMLParser):    
    def handle_starttag(self, tag, attrs):                
        for attr in attrs:
            pattern_href = "\/services\/(?P<service>\w+)\?wsdl"    
            value = attr[1]
            match = re.search(pattern_href, value)
            service =  match.group("service")            
            SERVICES_LOCAL.append(service)           
              
""" Nagios Helper 
"""
def exit(rc,msg):
    print "%s: %s" % (RC_TXT[rc], msg)
    sys.exit(rc)
    
"""
checkService(service):
service : String 
    Check if service is in baseline config

"""
def checkService(service):
    if service in SERVICES_LOCAL:        
        return True
    else:
        return False

"""
parseURL(url):
    url: string passed from argument
    
    Description:
        Check if url is formed as ip:port or just ip
"""        
def parseURL(url):
    port = PORT_DEFAULT    
    pattern_url = re.compile("^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    pattern_port = re.compile("^\d{1,5}$")
    #Check if we have Port in argument
    if ':' in url:
        port = url.split(':')[1]
        url = url.split(':')[0]       
    #Regex checking  
    if re.match(pattern_url,url):
        if re.match(pattern_port,port):
            port = int(port)
        else:
            raise Exception("Pattern not formed as a correct int")   
    else:
         raise Exception("URL not formed as a correct url pattern")      
    return (url,port)
       
"""
    readConfig(config_file)
        config_file: path to baseline file for services check    
    Description:
        Create an array with all services to be checked        
"""
def readConfig(config_file=BASE_CONFIG):
    services = False       
    f = open(config_file,'r')
    list = f.readlines()
    for line in list:
        if "SERVICES" in line:
            #services configured
            services = True
        elif services:
            service = line.strip()            
            SERVICES.append(service)
    
"""
    getHTML(url)
        url: string to html response
    Description:
        Get html string from url passed as argument.
"""    
def getHTML(url):
    content = ''
    try:
        response = urllib2.urlopen(url)    
        content = response.read()
    except urllib2.URLError, e:
        print e.message
    return content



if __name__ == '__main__':   
    parser = OptionParser()
    parser.add_option("-u","--url",
        dest="url",
        help="Valid IP: 192.168.10.10:8000 / 192.168.10.10:8080 . Port by default : 8000" ,
        default = None)    
    (options, args) = parser.parse_args()
    
    if options.url is None:
        print "Error: There is no URL as argument"
        sys.exit(2)
    else: 
        url = options.url
    #Reading Configurations
    readConfig()
    #Checking Arguments      
    url,port = parseURL(url)
    url_final = BASE_URL % (url,port)    
    #Downloading HTML file
    html_response = getHTML(url_final)
    if html_response == '' or 'Axis2: Services' not in html_response:
        rc = RC_CRIT
        msg = "There is no Configuration in URL or is not a service "        
    else:
        parser = MyHTMLParser()    
        parser.feed(html_response)
        msg = ""
        rc = RC_UNKNOWN
        for service in SERVICES:            
            if not checkService(service):            
                rc = RC_CRIT            
                msg += " %s not in configuration " % (service)
        if msg == "":
            rc = RC_OK
            msg = "All Services are up"
    exit(rc,msg)
    
    
    
    
    