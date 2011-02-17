#!/usr/bin/env python
import cgitb, cgi
import MySQLdb
import os
import json
cgitb.enable()    

print "Content-Type: application/json"     # HTML is following
print                               # blank line, end of headers

db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="realtime_sketch")
cur = db.cursor(MySQLdb.cursors.DictCursor)

form = cgi.FieldStorage()
taskId = int(form['task'].value)

cur.execute("""SELECT assignmentId, x, y, clicktime FROM clicks WHERE taskId = %s""", (taskId,))

clicks = []
for clickrow in cur.fetchall():
    clickrow['clicktime'] = float(clickrow['clicktime'])
    clicks.append(clickrow)
    
print json.dumps(clicks)    
    
cur.close()
db.close()