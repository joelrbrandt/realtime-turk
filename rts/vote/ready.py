from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection

from rts import rts_logging
import logging

from rtsutils.timeutils import unixtime
from datetime import datetime
from rts.video import location_ping
from rtsutils.get_photo import getSlowPhotos
import random


""" Writes to the request whether we need this particular worker to attack a video right now"""
def is_ready(request):
    request.content_type = "application/json"
    db = DBConnection()
    
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value
    workerid = form['workerid'].value
    
    result = getVideosNeedingVotes(db, workerid)
    
    if len(result) == 0:
        request.write(json.dumps( { 'is_ready' : False } ))
    else:
        # grab the most recent video upload
        videoid = result[0]['videoid']
        logging.debug("Videos needing votes: " + str(videoid))        
        locations = getSlowPhotos(videoid, 3)
        random.shuffle(locations)
        request.write(json.dumps(dict( videoid = videoid, photos = locations), cls = location_ping.DecimalEncoder))

def getVideosNeedingVotes(db, workerid):
    videos = db.query_and_return_array("""SELECT COUNT(*), study_videos.videoid FROM study_videos LEFT JOIN slow_votes ON slow_votes.videoid = study_videos.videoid WHERE slow_voting_available = TRUE GROUP BY study_videos.videoid HAVING COUNT(*) < 5 LIMIT 1""")
    
    videos = filter(lambda x: not haveCompleted(x['videoid'], workerid, db), videos)
    
    return videos
    
    
def haveCompleted(videoid, workerid, db):
    count = db.query_and_return_array("""SELECT COUNT(*) FROM slow_votes WHERE videoid = %s AND workerid = %s""", (videoid, workerid))
    return count[0]['COUNT(*)']