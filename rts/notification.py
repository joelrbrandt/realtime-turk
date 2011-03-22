from mod_python import util

import MySQLdb
from rtsutils.timeutils import parseISO
import settings
import logging
import sys, traceback

def notificationLogging(request):
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor()
    
    logging.info("Logging request.")    
    
    try:
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
        
        cur.execute("INSERT INTO notifications (eventtype, timestamp, hittypeid, hitid, assignmentid) VALUES (%s, %s, %s, %s, %s)""", (event_type, event_time, hit_type_id, hit_id, assignment_id))
    except Exception as e:
        logging.exception(str(e))
    
    cur.close()
    db.close()
