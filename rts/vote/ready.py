from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection

from rts import rts_logging
import logging

from rtsutils.timeutils import unixtime
from datetime import datetime
from rts.video import location_ping
from rtsutils.get_photo import getSlowPhotos
from rtsutils.vote_poster import getVideosNeedingVotes
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
        result = getAndAssignPhotos(videoid, assignmentid, db)
        request.write(json.dumps(result, cls = location_ping.DecimalEncoder))

def getAndAssignPhotos(videoid, assignmentid, db):
    updateAssignment(assignmentid, videoid)
    
    logging.debug("Videos needing votes: " + str(videoid))        
    locations = getSlowPhotos(videoid, 3)
    random.shuffle(locations)
    return dict( videoid = videoid, photos = locations, is_ready = True)    

    
def updateAssignment(assignmentid, videoid):
    """ Updates the database to map this video onto the assignment """
    db = DBConnection()
    try:
        db.query_and_return_array("""UPDATE assignments SET videoid = %s WHERE assignmentid = %s""", (videoid, assignmentid) )
    except:
        logging.exception("Error updating assignments table to set videoid")
    