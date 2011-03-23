from mod_python import util

import MySQLdb
from datetime import datetime
import time
from rtsutils.timeutils import *
import settings

import rts_logging
import logging

def log(request):
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor()
    
    form = util.FieldStorage(request)
    
    event = form['event'].value
    detail = form['detail'].value # e.g., word number
    text_id = int(form['textid'].value)
    assignment = form['assignmentid'].value
    hit = form['hitid'].value
    worker = form['workerid'].value
    experiment = int(form['experiment'].value)
    ip = request.connection.remote_ip
    useragent = request.headers_in['User-Agent']
    time = parseISO(form['time'].value)
    bucket = parseISO(form['bucket'].value)
    servertime = unixtime(datetime.now())
    
    # TODO: factor out of logging any information in the HITs or assignments table
    
    try:    
        cur.execute("""INSERT INTO logging (textid, event, detail, experiment, time, servertime, bucket, assignmentid, workerid, ip, useragent, hitid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", (text_id, event, detail, experiment, time,  servertime, bucket, assignment, worker, ip, useragent, hit))
        
        # if it's an accept event, we start logging information about it in our assignments table
        if event == "accept":
            cur.execute("""INSERT INTO assignments (assignmentid, workerid, hitid, textid, accept) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE `accept` = %s, `show` = NULL, `go` = NULL, `first` = NULL, `precision` = NULL, `recall` = NULL""", (assignment, worker, hit, text_id, time, time))
    except:
        logging.exception("Logging exception:")
    
    cur.close()
    db.close()
