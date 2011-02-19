#!/usr/bin/env python
import cgitb, cgi
import MySQLdb
import os
import json
cgitb.enable()    

print "Content-Type: application/json"     # HTML is following
print                               # blank line, end of headers

db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="wordclicker")
cur = db.cursor(MySQLdb.cursors.DictCursor)

form = cgi.FieldStorage()
textId = int(form['textid'].value)
trial = int(form['trial'].value)

cur.execute("""SELECT * FROM logging WHERE textid = %s AND trial = %s""", (textId, trial))

clicks = []
for clickrow in cur.fetchall():
    clickrow['time'] = float(clickrow['time'])
    clicks.append(clickrow)
    
print json.dumps(clicks)    
    
cur.close()
db.close()