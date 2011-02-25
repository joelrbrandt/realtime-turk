import MySQLdb
from timeutils import unixtime
from datetime import datetime, timedelta
import simplejson as json
from timeutils import parseISO

TEST_TEXT_PK = 25
EXPERIMENT = 12
MIN_BETWEEN_TESTS = 5
COLUMN = "time" # "servertime"

# TODO: fix logging so that we log which time window they're aiming for

# TODO: move sql query so that it gets executed for each window separately

def parseResults():    
    db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="wordclicker", use_unicode=True)
    cur = db.cursor()
    
    print("Format:")
    print("---bucket: time that bucket starts----")
    print("  time between bucket start and click received | time between text appear and user click | time between HIT accept and user click")
    print
    print
    
    timebuckets = dict()
    
    # initialize all the buckets
    cur.execute("""SELECT DISTINCT bucket FROM logging WHERE textid = %s AND experiment = %s AND event='highlight'"""  % (TEST_TEXT_PK, EXPERIMENT) )
    while True:
        row = cur.fetchone()
        if row == None:
            break

        bucket_time = datetime.fromtimestamp(row[0])
        timebuckets[bucket_time] = []        
    
    # get all the clicks
    for timebucket in sorted(timebuckets.keys()):
        cur.execute("""SELECT MIN(%s), workerid, detail, assignmentid from logging WHERE textid = %s AND experiment = %s AND event='highlight' AND time >= %s AND time < %s GROUP BY workerid""" % (COLUMN, TEST_TEXT_PK, EXPERIMENT, unixtime(timebucket), unixtime(timebucket + timedelta(minutes = MIN_BETWEEN_TESTS))) )
    
        for row in cur.fetchall():    
            click_time = datetime.fromtimestamp(row[0])
            
            # when did the worker accept that task?
            cur.execute("""SELECT %s from logging WHERE event='accept' AND assignmentid = '%s'""" % ( COLUMN, row[3] ))
            result = cur.fetchone()
            if result is not None:
                accept_time = datetime.fromtimestamp(result[0])
            else:
                accept_time = None
                
            timebuckets[timebucket].append({ 'click_time': click_time, 'workerid': row[1], 'detail': json.loads(row[2]), 'accept_time': accept_time })
     
    for key in sorted(timebuckets.keys()):
        print('-----bucket: ' + str(key) + '-----')
        for click in sorted(timebuckets[key], key=lambda k: k['click_time']):
            delta = total_seconds(click['click_time'] - key)
            
            appear_time = datetime.fromtimestamp(parseISO(click['detail']['showTime']))
            delta_since_appear = total_seconds(click['click_time'] - appear_time)

            delta_since_accept = None         
            if click['accept_time'] is not None:
                delta_since_accept = total_seconds(click['click_time'] - click['accept_time'])
            print('  ' + str(delta) + 'sec | ' + str(delta_since_appear) + 'sec | ' + str(delta_since_accept) + 'sec')
            
            
    print
    print
    print "worker lags"
    worker_lags = dict()
    # looking at per-user lag time
    for key in sorted(timebuckets.keys()):
        for click in sorted(timebuckets[key], key=lambda k: k['click_time']):
            if not worker_lags.has_key(click['workerid']):
                worker_lags[click['workerid']] = []
            
            delta = total_seconds(click['click_time'] - key)
            worker_lags[click['workerid']].append(delta)
    for workerid in worker_lags.keys():
        print(workerid + ' ' + str(worker_lags[workerid]))
        
    cur.close()
    db.close()        

def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0

parseResults()