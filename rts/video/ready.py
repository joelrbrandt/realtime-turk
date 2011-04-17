from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection
from rts.video import location_ping

from rts import rts_logging
import logging

from rtsutils.timeutils import unixtime
from datetime import datetime

from rtsutils.study_poster import unlabeledVideos

VIDEO_SOURCE_DIR = 'media/videos/'

""" Writes to the request whether we need this particular worker to attack a video right now"""
def is_ready(request):
    request.content_type = "application/json"
    db = DBConnection()
    
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value
    workerid = form['workerid'].value
    
    if form.has_key('videoid'):
        videoid = int(form['videoid'].value)        
    else:
        is_slow = form.has_key('slow') and form['slow'] == "1"
        result = unlabeledVideos(db, is_slow)

        if is_slow:
            # have I already labeled this video?
            result = filter(lambda x: not haveCompleted(x['pk'], workerid, db), result)
        
        if len(result) == 0:
            request.write(json.dumps( { 'is_ready' : False } ))
            return
        else:
            # grab the most recent video upload
            logging.debug("Videos needing labels: " + str(result))        
            videoid = result[0]['pk']

    video = getAndAssignVideo(assignmentid, videoid)        
    request.write(json.dumps(video, cls = location_ping.DecimalEncoder) )

def haveCompleted(videoid, workerid, db):
    """Only call this in the slow version"""
    count = db.query_and_return_array("""SELECT COUNT(*) FROM slow_snapshots, assignments WHERE videoid = %s AND slow_snapshots.assignmentid = assignments.assignmentid AND workerid = %s""", (videoid, workerid))
    return count[0]['COUNT(*)']

def getAndAssignVideo(assignmentid, videoid, restart_if_converged = False):
    """Gets the given video from the database, and populates a dict with its properties. Assigns the video to the worker in the database. """
    video = getVideo(videoid, restart_if_converged = restart_if_converged)
    updateAssignment(assignmentid, videoid)    
    return video

""" Gets a Python dict for the video """
def getVideo(videoid, restart_if_converged = False):
    db = DBConnection()
    result = db.query_and_return_array("""SELECT pk, width, height, filename, creationtime FROM videos WHERE pk = %s""", (videoid, ) )[0]

    json_out = dict(is_ready = True, width = result['width'],
                    height = result['height'], filename = result['filename'],
                    videoid = result['pk'], creationtime = result['creationtime'])
    
    # get or create a video labeling phase
    phase = location_ping.getMostRecentPhase(videoid, db, restart_if_converged = restart_if_converged)

    json_out['phase'] = phase

    return json_out

def updateAssignment(assignmentid, videoid):
    """ Updates the database to map this video onto the assignment """
    db = DBConnection()
    try:
        db.query_and_return_array("""UPDATE assignments SET videoid = %s WHERE assignmentid = %s""", (videoid, assignmentid) )
    except:
        logging.exception("Error updating assignments table to set videoid")
