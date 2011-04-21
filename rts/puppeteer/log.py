from mod_python import util

from datetime import datetime
import time
from rtsutils.timeutils import *

from rtsutils.db_connection import DBConnection
from rts import rts_logging
import logging

def log(request):
    db=DBConnection()
    
    form = util.FieldStorage(request)
    
    event = form['event'].value
    detail = form['detail'].value # e.g., word number
    assignment = form['assignmentid'].value
    worker = form['workerid'].value
    hit = form['hitid'].value
    ip = request.connection.remote_ip
    useragent = request.headers_in['User-Agent']
    time = parseISO(form['time'].value)
    servertime = unixtime(datetime.now())
    
    #logging.debug("Logging assignment %s event %s" % (assignment, event))
    
    try:    
        db.query_and_return_array("""INSERT INTO logging (event, detail, assignmentid, time, servertime, ip, useragent) VALUES (%s, %s, %s, %s, %s, %s, %s)""", (event, detail, assignment, time, servertime, ip, useragent))
        
        # if it's an accept event, we start logging information about it in our assignments table
        if event == "accept":
            db.query_and_return_array("""INSERT INTO assignments (assignmentid, workerid, hitid, accept) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE workerid = %s, `accept` = %s, `show` = NULL, `go` = NULL, `first` = NULL, `submit` = NULL, `points` = NULL""", (assignment, worker, hit, time, worker, time))
    except:
        logging.exception("Logging exception:")
    
