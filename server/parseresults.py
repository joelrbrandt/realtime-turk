import MySQLdb
from timeutils import unixtime
from datetime import datetime, timedelta
import simplejson as json
from timeutils import parseISO
import numpy
import settings

TEST_TEXT_PK = 25
EXPERIMENT = 17
MIN_BETWEEN_TESTS = 5
TIME_TO_BUCKETS = 5

# TODO: make the two columsn correctly identify client/server time

def parseResults():    
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE,
 use_unicode=True)
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
        cur.execute("""SELECT MIN(servertime), workerid, detail, assignmentid, time from logging WHERE textid = %s AND experiment = %s AND event='highlight' AND bucket = %s GROUP BY workerid""" % (TEST_TEXT_PK, EXPERIMENT, unixtime(timebucket)) )
    
        for row in cur.fetchall():    
            click_time = datetime.fromtimestamp(row[0])
            client_time = datetime.fromtimestamp(row[4])
            
            # when did the worker accept that task?
            cur.execute("""SELECT servertime from logging WHERE event='accept' AND assignmentid = '%s'""" % ( row[3] ))
            result = cur.fetchone()
            if result is not None:
                accept_time = datetime.fromtimestamp(result[0])
            else:
                accept_time = None
                
            timebuckets[timebucket].append({ 'click_time': click_time, 'workerid': row[1], 'detail': json.loads(row[2]), 'accept_time': accept_time, 'client_time': client_time })
    
    time_to = dict()
    for key in sorted(timebuckets.keys()):
        print('-----bucket: ' + str(key) + '-----')
        for index, click in enumerate(sorted(timebuckets[key], key=lambda k: k['click_time'])):
            delta = total_seconds(click['click_time'] - key)
            
            appear_time = datetime.fromtimestamp(parseISO(click['detail']['showTime']))
            delta_since_appear = total_seconds(click['client_time'] - appear_time)

            delta_since_accept = None         
            if click['accept_time'] is not None:
                delta_since_accept = total_seconds(click['click_time'] - click['accept_time'])
            print('  ' + str(delta) + 'sec | ' + str(delta_since_appear) + 'sec | ' + str(delta_since_accept) + 'sec')
            
            if not time_to.has_key(index+1):
                time_to[index+1] = []
            time_to[index+1].append(delta)
            
            
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
    
    print
    print
    print "aggregated (REMOVING FIRST BUCKET AS STARTUP)"    
    for i in range(1,TIME_TO_BUCKETS+1):
        # removes first bucket as probably noisy
        input_arr = time_to[i][1:]
        
        print("Time to " + str(i))
        print("\tMedian:" + str(numpy.median(input_arr)) + " Mean: " + str(numpy.mean(input_arr)) + " s.d.: " + str(numpy.std(input_arr)))
    
    cur.close()
    db.close()        

def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0

parseResults()
