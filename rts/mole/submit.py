from mod_python import apache, util
import json

from rtsutils.timeutils import parseISO, unixtime
from rtsutils.db_connection import DBConnection
from datetime import datetime

from rts import rts_logging
import logging

from ready import getMostRecentPhase, getMoleForAssignment, closePhase#, decideMole
from rtsutils.mole_poster import MIN_WHACKS_TO_DECIDE 

BASE_HIT_SUBMIT_URL = "http://www.mturk.com/mturk/externalSubmit?"

def record_and_redirect(request):
    query = request.parsed_uri[apache.URI_QUERY]
    logging.debug("got a submit request with query string = %s" % (str(query)))

    try:
        log_submission_in_db(request)
    except:
        logging.exception("got exception storing this submission in db:\n%s\n" % (str(query)))

    redirect_url = BASE_HIT_SUBMIT_URL + query
    util.redirect(request, redirect_url)

def log_submission_in_db(request):
    """
    Mapping of db columns (left) to form keys (right):
      assignmentid = assignmentId
      workerid = w
      mole = m
      accept = a
      show = sh
      go = g
      donewaiting = dw
      submit = su
    """

    form = util.FieldStorage(request)

    # Get all the items out of the form

    assignmentid = get_value_or_none(form, "assignmentId")
    workerid = get_value_or_none(form, "w")
    mole = get_value_or_none(form, "m")

    # Parse the times
    accept = get_time_or_none(form, "a")
    show = get_time_or_none(form, "sh")
    go = get_time_or_none(form, "g")
    donewaiting = get_time_or_none(form, "dw")
    mousemove = get_time_or_none(form, "mm")
    submit = get_time_or_none(form, "su")
    
    sql = """UPDATE `assignments` SET
            `show` = %s, `go` = %s, `donewaiting` = %s, `mousemove` = %s, `submit` = %s WHERE assignmentid = %s;
          """

    try:
        db=DBConnection()
        db.query_and_return_array(sql, (show, go, donewaiting, mousemove, submit, assignmentid))
        
        moleid = getMoleForAssignment(assignmentid, db)
        phase = getMostRecentPhase(moleid, db)
        
        sql = """INSERT INTO responses (moleid, phaseid, assignmentid, response) VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE response=%s"""        
        db.query_and_return_array(sql, (moleid, phase['pk'], assignmentid, mole, mole))
        
        result = db.query_and_return_array("""SELECT COUNT(*) FROM responses WHERE phaseid = %s""", (phase['pk'], ))
        if result[0]['COUNT(*)'] >= MIN_WHACKS_TO_DECIDE and phase['end'] == 0:
            closePhase(phase['pk'], unixtime(datetime.now()), db)
            #decideMole(phase['phase_list'], db)
        
    except:
        logging.exception("couldn't insert into the database")
    

def get_value_or_none(form, key):
    result = None
    try:
        result = form[key].value
    except:
        pass # didn't contain the key, or something else
    return result

def get_time_or_none(form, key):
    result = None
    try:
        result = parseISO(form[key].value)
    except:
        pass # didn't contain the key, or something else
    return result
