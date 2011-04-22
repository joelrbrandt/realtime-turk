from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection

from rts import rts_logging
import logging

from rtsutils.timeutils import unixtime
from datetime import datetime
import random


""" Writes to the request whether we need this particular worker to attack a video right now"""
def is_ready(request):
    request.content_type = "application/json"
    db = DBConnection()
    
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value
    workerid = form['workerid'].value

    w = db.query_and_return_array("SELECT * from work_available");
    if len(w) > 0:
        updateAssignment(assignmentid)
        request.write(json.dumps( { 'is_ready' : True } ))
    else:
        request.write(json.dumps( { 'is_ready' : False } ))

def updateAssignment(assignmentid):
    """ Updates the database to say whether this assignment had real work associated with it """
    db = DBConnection()
    try:
        db.query_and_return_array("""UPDATE assignments SET was_real_work=1 WHERE assignmentid = %s""", (assignmentid,) )
    except:
        logging.exception("Error updating assignments table to set videoid")
    
