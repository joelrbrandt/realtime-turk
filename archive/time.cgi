#!/usr/bin/env python
import cgitb, cgi
from datetime import datetime
import time
from timeutils import *
cgitb.enable()    

print "Content-type: application/json"     # HTML is following
print                               # blank line, end of headers

now = unixtime(datetime.now()) * 1000 # javascript uses millis, not seconds
print "{ \"date\": \"%f\" }" % now