import MySQLdb
from timeutils import unixtime
from datetime import datetime, timedelta
import simplejson as json
from timeutils import parseISO
import numpy
import settings

TEST_TEXT_PK = 25
EXPERIMENT = 18
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
        cur.execute("""SELECT MIN(time), workerid, detail, assignmentid, servertime from logging WHERE textid = %s AND experiment = %s AND event='highlight' AND bucket = %s GROUP BY workerid""" % (TEST_TEXT_PK, EXPERIMENT, unixtime(timebucket)) )
    
        for row in cur.fetchall():    
            answer_time = { 'client': datetime.fromtimestamp(row[0]),
                            'server': datetime.fromtimestamp(row[4]) }
            
            # when did the worker accept that task?
            cur.execute("""SELECT time, servertime from logging WHERE event='accept' AND assignmentid = '%s'""" % ( row[3] ))
            result = cur.fetchone()
            if result is not None:
                accept_time = { 'client': datetime.fromtimestamp(result[0]),
                                'server': datetime.fromtimestamp(result[1]) }
            else:
                accept_time = None
                
            # when did the task or 'go' button appear to the user?
            detail = json.loads(row[2])
            show_time = { 'client': datetime.fromtimestamp(parseISO(detail['showTime'])) } # no server time
                
            # when did the worker click the "go" button?
            cur.execute("""SELECT time, servertime from logging WHERE event='go' AND assignmentid = '%s'""" % ( row[3] ))
            result = cur.fetchone()
            if result is not None:
                go_time = { 'client': datetime.fromtimestamp(result[0]),
                            'server': datetime.fromtimestamp(result[1]) }
            else:
                go_time = None
            
                
            timebuckets[timebucket].append({ 'answer_time': answer_time,
                                            'workerid': row[1],
                                            'detail': json.loads(row[2]),
                                            'accept_time': accept_time,
                                            'show_time': show_time,
                                            'go_time': go_time })
    
    time_to = dict()
    for key in sorted(timebuckets.keys()):
        print('-----bucket: ' + str(key) + '-----')
        for index, click in enumerate(sorted(timebuckets[key], key=lambda k: k['answer_time']['server'])):
            answer_delta_bucket = total_seconds(click['answer_time']['server'] - key)
            
            answer_delta_go = total_seconds(click['answer_time']['client'] - go_time['client'])
            go_delta_show = total_seconds(click['go_time']['client'] - click['show_time']['client'])

            #             accept_delta_answer = None         
            #             if click['client_accept_time'] is not None:
            #                 delta_since_accept = total_seconds(click['click_time']['client'] - click['accept_time']['client'])
            print('answer-bucket  ' + str(answer_delta_bucket) + 'sec | go-show ' + str(go_delta_show) + 'sec | answer-go ' + str(answer_delta_go) + 'sec')
            
            if not time_to.has_key(index+1):
                time_to[index+1] = []
            time_to[index+1].append(answer_delta_bucket)
            
            
    print
    print
    print "worker lags"
    worker_lags = dict()
    # looking at per-user lag time
    for key in sorted(timebuckets.keys()):
        for click in sorted(timebuckets[key], key=lambda k: k['answer_time']['server']):
            if not worker_lags.has_key(click['workerid']):
                worker_lags[click['workerid']] = []
            
            delta = total_seconds(click['answer_time']['server'] - key)
            worker_lags[click['workerid']].append(delta)
    for workerid in worker_lags.keys():
        print(workerid + ' ' + str(worker_lags[workerid]))
    
    print
    print
    print "aggregated (REMOVING FIRST BUCKET AS STARTUP)"    
    for i in range(1,TIME_TO_BUCKETS+1):
        if time_to.has_key(i):
            # removes first bucket as probably noisy
            input_arr = time_to[i][1:]
            
            print("Time to " + str(i))
            print("\tMedian:" + str(numpy.median(input_arr)) + " Mean: " + str(numpy.mean(input_arr)) + " s.d.: " + str(numpy.std(input_arr)))
    
    cur.close()
    db.close()        

def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0

parseResults()
