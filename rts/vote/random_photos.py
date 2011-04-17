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

def getRandomPhotos(request):
    request.content_type = "application/json"
    form = util.FieldStorage(request)
    
    db = DBConnection()
    assignmentid = form['assignmentid']
    if form.has_key('videoid'):
        videoid = int(form['videoid'].value)
    else:        
        logging.debug("Getting random photos")
        
        videoid = db.query_and_return_array("""SELECT COUNT(*), videos.pk FROM videos, slow_snapshots, assignments WHERE videos.pk NOT IN (SELECT videoid FROM study_videos) AND slow_snapshots.assignmentid = assignments.assignmentid AND assignments.videoid = videos.pk AND videos.pk <> 1 GROUP BY videos.pk HAVING COUNT(*) > 1""")[0]['pk']
        #videoid = db.query_and_return_array("""SELECT videoid, COUNT(*) FROM slow_votes, assignments WHERE slow_votes.assignmentid = assignments.assignmentid GROUP BY videoid HAVING COUNT(*) > %s ORDER BY RAND() LIMIT 1""", (MIN_VOTES, ))[0]['videoid']
            

    result = ready.getAndAssignPhotos(videoid, assignmentid, db)
    request.write(json.dumps(result, cls = DecimalEncoder))
