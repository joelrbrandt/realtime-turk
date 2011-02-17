#!/usr/bin/env python
import cgitb, cgi
from datetime import datetime
import time
from timeutils import *
import MySQLdb
import os
import json
cgitb.enable()    

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers

db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="realtime_sketch")
cur = db.cursor()

form = cgi.FieldStorage()
clicks = json.loads(form['clicks'].value)
assignment = form['assignmentId'].value
ip = cgi.escape(os.environ["REMOTE_ADDR"])
task = form['taskId'].value

for click in clicks:
    x = int(click['x'])
    y = int(click['y'])
    time = parseISO(click['time'])
    
    cur.execute("""INSERT INTO clicks (x, y, clicktime, assignmentId, ip, taskId) VALUES (%s, %s, %s, %s, %s, %s)""", (x, y, time, assignment, ip, task))
    
cur.close()
db.close()