#!/usr/bin/env python
import cgitb, cgi
import time
from datetime import datetime
from timeutils import *
import MySQLdb
import os
cgitb.enable()    

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers

db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="realtime_turk")
cur = db.cursor()

form = cgi.FieldStorage()
if "requestTime" in form:
    request = parseISO(form["requestTime"].value)
    
    cur.execute("""INSERT INTO views (requesttime, requeststring, ip, assignmentId) 
                   VALUES (%s, %s, %s, %s)""", 
                    (request, form["requestTimeString"].value, cgi.escape(os.environ["REMOTE_ADDR"]),
                    form["assignmentId"].value))
    
cur.close()
db.close()