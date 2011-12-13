from mod_python import apache, util
import json

from rts import rts_logging
import logging
from rts.video.location_ping import DecimalEncoder
from rtsutils.timeutils import unixtime

from rtsutils.db_connection import DBConnection
import ready

from datetime import datetime, timedelta

def getRandomMole(request):
    request.content_type = "application/json"
    form = util.FieldStorage(request)
    
    db = DBConnection()
    assignmentid = form['assignmentid']
    if form.has_key('moleid'):
        moleid = int(form['moleid'].value)
    else:        
        logging.debug("Getting random mole")
        
        moleid = db.query_and_return_array("""SELECT * FROM moles ORDER BY RAND() LIMIT 1""")[0]
            

    result = ready.getAndAssignMole(moleid, assignmentid, db)
    request.write(json.dumps(result, cls = DecimalEncoder))
