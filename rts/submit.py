from mod_python import apache, util
import MySQLdb
import simplejson as json
import settings

from rtsutils.timeutils import parseISO

import rts_logging
import logging

from rtsutils import word_clicker_approver

#BASE_HIT_SUBMIT_URL = "http://planetexpress.stanford.edu/foo.php?"
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
      experiment = e
      textid = t
      wordarray = wa
      accept = a
      show = sh
      go = g
      first = f
      submit = su

    db column names that must be computed
      precision
      recall
    """

    """ TODO: add calculation of total focus/blur time to the submission process
              we'll parse this out of the log table and add it to the submission page
    """

    form = util.FieldStorage(request)

    # Get all the items out of the form

    assignmentid = get_value_or_none(form, "assignmentId")
    workerid = get_value_or_none(form, "w")
    experiment = get_value_or_none(form, "e")
    textid = get_value_or_none(form, "t")
    wordarray = get_value_or_none(form, "wa")
    precision = None
    recall = None

    # Parse the times
    accept = get_time_or_none(form, "a")
    show = get_time_or_none(form, "sh")
    go = get_time_or_none(form, "g")
    first = get_time_or_none(form, "f")
    submit = get_time_or_none(form, "su")
    

    # Parse the word array and compute precision/recall
    try:
        if wordarray != None and textid != None:
            wordarray_parsed = json.loads(wordarray)
            d = word_clicker_approver.calculateAccuracy(textid, wordarray_parsed)
            precision = d['precision']
            recall = d['recall']
    except:
        logging.exception("Error parsing word array or getting precision/recall")

    sql = """UPDATE `assignments` SET
              `wordarray` = %s, `show` = %s, `go` = %s, `first` = %s, `submit` = %s, `precision` = %s, `recall` = %s
              WHERE assignmentid = %s;
          """

    try:
        db=MySQLdb.connect(host=settings.DB_HOST, 
                           passwd=settings.DB_PASSWORD,
                           user=settings.DB_USER,
                           db=settings.DB_DATABASE,
                           use_unicode=True)
        cur = db.cursor()
        cur.execute(sql, (wordarray, show, go, first, submit, precision, recall, assignmentid))
        cur.close()
        db.close()
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

