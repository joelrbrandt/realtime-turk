from mod_python import apache, util
import simplejson as json

from rtsutils.db_connection import DBConnection
from rts.video import location_ping

from rts import rts_logging
import logging

from rtsutils.timeutils import unixtime
from datetime import datetime

VIDEO_SOURCE_DIR = 'media/videos/'

""" Writes to the request whether we need this particular worker to attack a video right now"""
def is_ready(request):
    request.content_type = "application/json"
    db = DBConnection()
    
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value
    workerid = form['workerid'].value
    
    # we need videos that have no pictures yet
    result = db.query_and_return_array("""
        SELECT pk FROM videos
        
        LEFT JOIN (SELECT COUNT(*) AS numPictures, 
        videoid FROM pictures GROUP BY videoid)
        AS pictureCount
        ON pictureCount.videoid = videos.pk        
        
        WHERE pictureCount.numPictures IS NULL
        
        ORDER BY videos.pk DESC """)

    if len(result) == 0:
        request.write(json.dumps( { 'is_ready' : False } ))
    else:
        # grab the most recent video upload
        logging.debug("Videos needing labels: " + str(result))        
        videoid = result[0]['pk']
        video = getAndAssignVideo(assignmentid, videoid)
        
        request.write(json.dumps(video, use_decimal = True) )

def getAndAssignVideo(assignmentid, videoid):
    """Gets the given video from the database, and populates a dict with its properties. Assigns the video to the worker in the database. """
    video = getVideo(videoid)
    updateAssignment(assignmentid, videoid)    
    return video

""" Gets a Python dict for the video """
def getVideo(videoid):
    db = DBConnection()
    result = db.query_and_return_array("""SELECT pk, width, height, filename FROM videos WHERE pk = %s""", (videoid, ) )[0]

    json_out = dict(is_ready = True, width = result['width'],
                    height = result['height'], filename = result['filename'],
                    videoid = result['pk'])
    
    # get or create a video labeling phase
    phase = location_ping.getMostRecentPhase(videoid, db)

    json_out['phase'] = phase

    return json_out

def updateAssignment(assignmentid, videoid):
    """ Updates the database to map this video onto the assignment """
    db = DBConnection()
    try:
        db.query_and_return_array("""UPDATE assignments SET videoid = %s WHERE assignmentid = %s""", (videoid, assignmentid) )
    except:
        logging.exception("Error updating assignments table to set videoid")
