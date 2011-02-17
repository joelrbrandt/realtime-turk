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
word_id = int(form['wordid'].value[4:]) # e.g., "word11"
text_id = int(form['textid'].value)
assignment = form['assignmentid'].value
trial = int(form['trial'].value)
highlighted = (form['highlighted'].value == "true")
ip = cgi.escape(os.environ["REMOTE_ADDR"])
time = parseISO(form['time'].value)
    
cur.execute("""INSERT INTO logging (textid, wordid, highlighted, time, assignmentid, ip, trial) VALUES (%s, %s, %s, %s, %s, %s, %s)""", (text_id, word_id, highlighted, time, assignment, ip, trial))

cur.close()
db.close()