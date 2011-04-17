from mod_python import apache, util
import json

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
    
    is_slow = False
    if form.has_key('slow') and form['slow'] == "1":
        is_slow = True
    
    videoid = None
    
    db = DBConnection()
    if form.has_key('videoid'):
        videoid = int(form['videoid'].value)
    else:
        if not is_slow:
            # are there any videos with incomplete phases that we can join?
            # grab the most recently touched one
            sql = """
                SELECT videoid FROM phases, phase_lists
                WHERE end IS NULL AND is_abandoned = 0 AND start >= %s
                AND phases.phase_list = phase_lists.pk
                ORDER BY start DESC LIMIT 1
                """
            max_age = unixtime(datetime.now() - timedelta(seconds = location_ping.PHASE_MAX_AGE_IN_SECONDS))
            unfinished_phases = db.query_and_return_array(sql, (max_age, ) )
            if len(unfinished_phases) > 0:
                videoid = unfinished_phases[0]['videoid']
        
        if is_slow or videoid is None:
            # TODO: this will not scale once we have over ~10,000 rows
            logging.debug("Getting random video")

            # get a video that's not in the study            

            # warning! HACK!
            logging.debug("HACK! ONLY RANDOM VIDEOS ARE THOSE with pk < 100")
            
            videoid = db.query_and_return_array("""SELECT pk FROM videos LEFT JOIN study_videos ON videos.pk = study_videos.videoid WHERE study_videos.videoid IS NULL """ + """ AND pk < 100 """ + 
            """ ORDER BY RAND() LIMIT 1""")[0]['pk']
            
    video_json = ready.getAndAssignPhotos(assignmentid, videoid, db)
    request.write(json.dumps(video_json, cls = location_ping.DecimalEncoder))
