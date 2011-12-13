from mod_python import apache, util
import json

from rts import rts_logging
import logging
from rts.video.location_ping import DecimalEncoder
from rtsutils.vote_poster import MIN_VOTES
from rtsutils.timeutils import unixtime

from rtsutils.db_connection import DBConnection
import ready

from datetime import datetime, timedelta

def getRandomVote(request):
    request.content_type = "application/json"
    form = util.FieldStorage(request)
    
    db = DBConnection()
    assignmentid = form['assignmentid']
    if form.has_key('voteid'):
        voteid = int(form['voteid'].value)
    else:        
        logging.debug("Getting random vote")
        
        voteid = db.query_and_return_array("""SELECT * FROM votes ORDER BY RAND() LIMIT 1""")[0]
            

    result = ready.getAndAssignVote(voteid, assignmentid, db)
    request.write(json.dumps(result, cls = DecimalEncoder))
