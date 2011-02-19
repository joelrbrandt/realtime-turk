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

db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="wordclicker")
cur = db.cursor()

form = cgi.FieldStorage()
event = form['event'].value
detail = form['detail'].value # e.g., word number
text_id = int(form['textid'].value)
assignment = form['assignmentid'].value
worker = form['workerid'].value
experiment = int(form['experiment'].value)
ip = cgi.escape(os.environ["REMOTE_ADDR"])
useragent = os.environ["HTTP_USER_AGENT"]
time = parseISO(form['time'].value)
servertime = unixtime(datetime.now())
    
cur.execute("""INSERT INTO logging (textid, event, detail, experiment, time, servertime, assignmentid, workerid, ip, useragent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (text_id, event, detail, experiment, time,  servertime, assignment, worker, ip, useragent))

cur.close()
db.close()