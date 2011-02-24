#!/usr/bin/env python
import cgitb, cgi
from datetime import datetime
import time
import json
from timeutils import *
cgitb.enable()    

print "Content-type: application/json"     # HTML is following
print                               # blank line, end of headers

now = round(unixtime(datetime.now()) * 1000) # javascript uses millis, not seconds
print json.dumps({'date': now })#"{ \"date\": \"%f\" }" % now