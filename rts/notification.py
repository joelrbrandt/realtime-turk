from mod_python import util

from rtsutils.timeutils import parseISO
from rtsutils.db_connection import DBConnection

import settings
import logging
import sys, traceback

def notificationLogging(request):
    db= DBConnection()

    form = util.FieldStorage(request)
    event_type = form['Event.1.EventType'].value
    event_time = parseISO(form['Event.1.EventTime'].value)
    hit_type_id = form['Event.1.HITTypeId'].value
    hit_id = form['Event.1.HITId'].value
    assignment_id = None
    if form.has_key('Event.1.AssignmentId'):
        assignment_id = form['Event.1.AssignmentId'].value

    #TODO: check to make sure we never get "event.2.eventtype" etc.
    logging.info("Event notification from MTurk: " + str(event_type) + " " + str(event_time) + " " + str(hit_type_id) + " " + str(hit_id) + " " + str(assignment_id))
    
    try:
        db.query_and_return_array("INSERT INTO notifications (eventtype, timestamp, hittypeid, hitid, assignmentid) VALUES (%s, %s, %s, %s, %s)""", (event_type, event_time, hit_type_id, hit_id, assignment_id))
        logging.error("WE INSERTED INTO NOTIFICATIONS IN DB " + settings.DB_DATABASE)
        
        if event_type == "AssignmentReturned":
            db.query_and_return_array("""UPDATE `assignments` SET `return` = %s WHERE `assignmentid` = %s;""", (event_time, assignment_id))
            
    except Exception:
        logging.exception("Notification exception")
