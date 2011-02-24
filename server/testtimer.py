from mod_python import apache, util

import MySQLdb
import simplejson as json
from datetime import datetime
from timeutils import *

MIN_BETWEEN_TESTS = 5
DESIRED_WORKERS = 5

def testTimer(request):
    request.content_type = "application/json"
    
    db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="wordclicker", use_unicode=True)
    cur = db.cursor()
    
    form = util.FieldStorage(request)
    workerid = unicode(form['workerid'].value)
    experimentid = int(form['experimentid'].value)
    test_text_pk = int(form['textid'].value)
    
    # first, determine if we have hit a new test timestamp
    now = datetime.now()
    last_test_mark = unixtime(now) - (unixtime(now) % (60*MIN_BETWEEN_TESTS))
    cur.execute("""SELECT DISTINCT workerid from logging WHERE time >= %s AND textid = 25 AND experiment = %s AND event='highlight'""" % (last_test_mark, experimentid) )
    completed = [row[0] for row in cur.fetchall()]
    
    if len(completed) >= DESIRED_WORKERS or unicode(workerid) in completed:
         # if we have enough workers or if you've already done the task
        request.write(json.dumps( { 'test' : False } ))
    else:       
        cur.execute("""SELECT text FROM texts WHERE pk = %s""", (test_text_pk,))
        
        text = cur.fetchone()[0]
        
        result = dict()
        result['pk'] = test_text_pk
        result['text'] = htmlizeText(text)
        result['test'] = True
        result['bucket'] = last_test_mark * 1000 # javascript likes millis
        
        request.write(json.dumps(result))
        
    cur.close()
    db.close()

# copied from gettext.cgi, since we can't import another CGI script
def htmlizeText(text):
    import nltk # do this lazily, we want this to return fast
    #print text.encode('ascii', 'replace')
    tokenized = nltk.tokenize.word_tokenize(text)
    
    spanned = []
    for index, token in enumerate(tokenized):
    #    print token.encode('ascii', 'replace') + " " + str(type(token))
        span = u"<span id='word" + unicode(index) +  u"' class='word'>" + token + u"</span>"
        spanned.append(span)
    
    paragraph = u"<p>" + u" ".join(spanned) + u"</p>"
    #print paragraph.encode('ascii', 'replace')
    return paragraph
