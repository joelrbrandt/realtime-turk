#!/usr/bin/env python
import cgitb, cgi
from datetime import datetime
import time
from timeutils import *
import MySQLdb
import os
cgitb.enable()    

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers

db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="realtime_turk")
cur = db.cursor()

form = cgi.FieldStorage()
if "clickTime" in form and "requestTime" in form:
    clicked = parseISO(form["clickTime"].value)
    print form["clickTime"].value
    print '%f' % clicked

    now = unixtime(datetime.now())
    
    request = parseISO(form["requestTime"].value)
    
    cur.execute("""INSERT INTO timing (requesttime, requeststring, clicktime,
                   servertime, ip, assignmentId) VALUES (%s, %s, %s, %s, %s, %s)""", 
                    (request, form["requestTimeString"].value, clicked, now, cgi.escape(os.environ["REMOTE_ADDR"]), form["assignmentId"].value))
    
cur.close()
db.close()