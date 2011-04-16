from mod_python import apache, util
import simplejson

from rts import rts_logging
import logging
from rtsutils.db_connection import DBConnection

import submit
from rtsutils.study_poster import PHOTOGRAPHER_ID

def slowSubmit(request):
    """ Handles submissions from the "slow" server """

    form = util.FieldStorage(request)
    # Get relevant items out of the form
    assignmentid = submit.get_value_or_none(form, "assignmentId")
    workerid = submit.get_value_or_none(form, "w")    
    snapshots_raw = submit.get_value_or_none(form, "sn")

    snapshots = simplejson.loads(snapshots_raw)
    logging.debug("SNAPSHOTS: %s" % snapshots)    

    db = DBConnection()
    
    for snapshot in snapshots:
        db.query_and_return_array("""INSERT INTO slow_snapshots (assignmentid, location) VALUES (%s, %s)""", (assignmentid, snapshot) )

    if workerid == PHOTOGRAPHER_ID:
        # photographer doesn't submit a HIT :)
        submit.log_submission_in_db(request)
        request.write("OK, got it! %s for %s" % (snapshots, assignmentid))
    else:
        submit.record_and_redirect(request)