from mod_python import apache, util
import json

from rts import rts_logging
import logging
from rtsutils.timeutils import unixtime

from rtsutils.db_connection import DBConnection
import ready

from datetime import datetime, timedelta

def getRandomWork(request):
    request.content_type = "application/json"

    form = util.FieldStorage(request)
    
    db = DBConnection()
    assignmentid = form['assignmentid']
    
    result = { "puppet": "human", "is_ready" : True }
    request.write(json.dumps(result))
