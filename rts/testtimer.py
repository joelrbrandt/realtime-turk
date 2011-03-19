from mod_python import apache, util

import MySQLdb
import simplejson as json
from datetime import datetime
from rtsutils.timeutils import *
import settings

MIN_BETWEEN_TESTS = 5

def testTimer(request):
    request.content_type = "application/json"
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE,
 use_unicode=True)
    cur = db.cursor()
    
    form = util.FieldStorage(request)
    workerid = unicode(form['workerid'].value)
    experimentid = int(form['experimentid'].value)
    test_text_pk = int(form['textid'].value)
    
    # first, determine if we have hit a new test timestamp
    now = datetime.now()
    last_test_mark = unixtime(now) - (unixtime(now) % (60*MIN_BETWEEN_TESTS))
    cur.execute("""SELECT DISTINCT workerid FROM logging WHERE time >= %s AND textid = %s AND experiment = %s AND event='highlight'""" % (last_test_mark, test_text_pk, experimentid) )
    completed = [row[0] for row in cur.fetchall()]
    
    if unicode(workerid) in completed:
         # if we have enough workers or if you've already done the task
        request.write(json.dumps( { 'test' : False } ))
    else:       
        cur.execute("""SELECT html FROM texts WHERE pk = %s""", (test_text_pk,))
        text = cur.fetchone()[0]
        
        result = dict()
        result['pk'] = test_text_pk
        result['text'] = text
        result['test'] = True
        result['bucket'] = last_test_mark * 1000 # javascript likes millis
        
        request.write(json.dumps(result))
        
    cur.close()
    db.close()
