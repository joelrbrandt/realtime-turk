from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection

from rts import rts_logging
import logging

from rtsutils.timeutils import *
from datetime import datetime

def numRetainerWorkers(request):
    request.content_type = "application/json"
    db = DBConnection()

    ping_floor = unixtime(datetime.now() - timedelta(seconds = 10))
    
    sql = """SELECT logging.assignmentid, logging.servertime FROM logging, 
        (SELECT MAX(servertime) AS pingtime, assignmentid FROM logging WHERE servertime > %s AND event LIKE 'ping%%' GROUP BY assignmentid) as mostRecent 
    WHERE logging.servertime = mostRecent.pingTime AND logging.assignmentid=mostRecent.assignmentid AND event = 'ping-waiting' GROUP BY assignmentid"""
    result = db.query_and_return_array(sql, (ping_floor, ))
    output = { 'num_waiting': len(result) }

    request.write(json.dumps(output))
