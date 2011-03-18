from mod_python import apache, util
import MySQLdb
import simplejson as json
import settings

import rts_logging
import logging

BASE_HIT_SUBMIT_URL = "http://planetexpress.stanford.edu/foo.php?"
#BASE_HIT_SUBMIT_URL = "http://www.mturk.com/mturk/externalSubmit"

def record_and_redirect(request):
    query = request.parsed_uri[apache.URI_QUERY]
    logging.debug("got a submit request with query string = " + str(query))
    redirect_url = BASE_HIT_SUBMIT_URL + query
    util.redirect(request, redirect_url)
