import MySQLdb
from timeutils import unixtime
from datetime import datetime, timedelta
import json
from timeutils import parseISO

TEST_TEXT_PK = 25
EXPERIMENT = 11
MIN_BETWEEN_TESTS = 5

# TODO: fix logging so that we log which time window they're aiming for

# TODO: move sql query so that it gets executed for each window separately

def parseResults():    
    db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="wordclicker", use_unicode=True)
    cur = db.cursor()
    
    print("Format:")
    print("---bucket: time that bucket starts----")
    print("  time between bucket start and click received / time between text appear and user click")
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
        cur.execute("""SELECT MIN(time), workerid, detail, assignmentid from logging WHERE textid = %s AND experiment = %s AND event='highlight' AND time >= %s AND time < %s GROUP BY workerid""" % (TEST_TEXT_PK, EXPERIMENT, unixtime(timebucket), unixtime(timebucket + timedelta(minutes = MIN_BETWEEN_TESTS))) )
    
        for row in cur.fetchall():    
            click_time = datetime.fromtimestamp(row[0])
            
            # when did the worker accept that task?
            #cur.execute("""SELECT time from logging WHERE event='accept' AND assignmentid = '%s'""" % ( row[3], ))
            #accept_time = unixtime(cur.fetchone()[0])
            
            timebuckets[timebucket].append({ 'click_time': click_time, 'workerid': row[1], 'detail': json.loads(row[2]) }) #, 'accept_time': accept_time })
     
    for key in sorted(timebuckets.keys()):
        print('-----bucket: ' + str(key) + '-----')
        for click in sorted(timebuckets[key]):
            delta = (click['click_time'] - key).total_seconds()
            
            appear_time = datetime.fromtimestamp(parseISO(click['detail']['showTime']))
            delta_since_appear = (click['click_time'] - appear_time).total_seconds()
            print('  ' + str(delta) + 'sec | ' + str(delta_since_appear) + 'sec')
            
            
    print
    print
    print "worker lags"
    worker_lags = dict()
    # looking at per-user lag time
    for key in sorted(timebuckets.keys()):
        for click in sorted(timebuckets[key]):
            if not worker_lags.has_key(click['workerid']):
                worker_lags[click['workerid']] = []
            
            delta = (click['click_time'] - key).total_seconds()
            worker_lags[click['workerid']].append(delta)
    for workerid in worker_lags.keys():
        print(workerid + ' ' + str(worker_lags[workerid]))
        
    cur.close()
    db.close()        

parseResults()