from mod_python import apache, util
import json

from rtsutils.timeutils import parseISO
from rtsutils.db_connection import DBConnection

from rts import rts_logging
import logging

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
      framearray = fa
      accept = a
      show = sh
      go = g
      submit = su
    """

    """ TODO: add calculation of total focus/blur time to the submission process
              we'll parse this out of the log table and add it to the submission page
    """

    form = util.FieldStorage(request)

    # Get all the items out of the form

    assignmentid = get_value_or_none(form, "assignmentId")
    workerid = get_value_or_none(form, "w")
    framearray = get_value_or_none(form, "fa")

    # Parse the times
    accept = get_time_or_none(form, "a")
    show = get_time_or_none(form, "sh")
    go = get_time_or_none(form, "g")
    submit = get_time_or_none(form, "su")
    

    sql = """UPDATE `assignments` SET
              `framearray` = %s, `show` = %s, `go` = %s, `submit` = %s WHERE assignmentid = %s;
          """

    try:
        db=DBConnection()
        db.query_and_return_array(sql, (framearray, show, go, submit, assignmentid))
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

