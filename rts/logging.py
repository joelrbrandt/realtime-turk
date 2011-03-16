from mod_python import util

import MySQLdb
from datetime import datetime
import time
from timeutils import *
import settings

def log(request):
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor()
    
    form = util.FieldStorage(request)
    event = form['event'].value
    detail = form['detail'].value # e.g., word number
    text_id = int(form['textid'].value)
    assignment = form['assignmentid'].value
    worker = form['workerid'].value
    experiment = int(form['experiment'].value)
    ip = request.connection.remote_ip
    useragent = request.headers_in['User-Agent']
    time = parseISO(form['time'].value)
    bucket = parseISO(form['bucket'].value)
    servertime = unixtime(datetime.now())
        
    cur.execute("""INSERT INTO logging (textid, event, detail, experiment, time, servertime, bucket, assignmentid, workerid, ip, useragent) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (text_id, event, detail, experiment, time,  servertime, bucket, assignment, worker, ip, useragent))
    
    cur.close()
    db.close()
