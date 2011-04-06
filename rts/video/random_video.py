from mod_python import apache, util
import simplejson as json

from rts import rts_logging
import logging
import location_ping
from rtsutils.timeutils import unixtime

from rtsutils.db_connection import DBConnection
import ready

from datetime import datetime, timedelta

def getRandomVideo(request):
    request.content_type = "application/json"
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value
    
    db = DBConnection()    
    if form.has_key('videoid'):
        videoid = int(form['videoid'].value)
    else:
        # are there any videos with incomplete phases that we can join?
        # grab the most recently touched one
        sql = """
            SELECT phase, videoid, MAX(servertime) FROM locations WHERE phase IN 
            (SELECT phase FROM phases
            WHERE end IS NULL AND is_abandoned = 0 AND start >= %s)
            GROUP BY phase
            ORDER BY MAX(servertime) DESC
        """
        max_age = unixtime(datetime.now() - timedelta(seconds = location_ping.PHASE_MAX_AGE_IN_SECONDS))
        unfinished_phases = db.query_and_return_array(sql, (max_age, ) )
        if len(unfinished_phases) > 0:
            videoid = unfinished_phases[0]['videoid']
        else:    
            # TODO: this will not scale once we have over ~10,000 rows
            logging.debug("Getting random video")
            videoid = db.query_and_return_array("""SELECT pk FROM videos ORDER BY RAND() LIMIT 1""")[0]['pk']
        
    video_json = ready.getAndAssignVideo(assignmentid, videoid, restart_if_converged = True)
    request.write(json.dumps(video_json, use_decimal=True))
