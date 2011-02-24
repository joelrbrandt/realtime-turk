import MySQLdb
from timeutils import unixtime
from datetime import datetime

TEST_TEXT_PK = 25
EXPERIMENT = 10
MIN_BETWEEN_TESTS = 5

# TODO: fix logging so that we log which time window they're aiming for

# TODO: move sql query so that it gets executed for each window separately

def parseResults():    
    db=MySQLdb.connect(host="mysql.csail.mit.edu", passwd="gangsta2125", user="realtime", db="wordclicker", use_unicode=True)
    cur = db.cursor()
    
    timebuckets = dict()
    cur.execute("""SELECT MIN(time), workerid from logging WHERE textid = %s AND experiment = %s AND event='highlight' GROUP BY workerid""" % (TEST_TEXT_PK, EXPERIMENT) )
    
    while(True):
        row = cur.fetchone()
        if row == None:
            break

        click_time = datetime.fromtimestamp(row[0])
        test_mark = datetime.fromtimestamp( unixtime(click_time) - (unixtime(click_time) % (60*MIN_BETWEEN_TESTS)) )
        
        if not timebuckets.has_key(test_mark):
            timebuckets[test_mark] = []
        timebuckets[test_mark].append({ 'click_time': click_time, 'workerid': row[1], 'click_raw': row[0] })
        
    for key in sorted(timebuckets.keys()):
        print('-----bucket: ' + str(key) + '-----')
        for click in sorted(timebuckets[key]):
            delta = (click['click_time'] - key).total_seconds()
            print('  ' + str(delta) + 'sec' + ' ' + str(click['click_raw']))
        
    cur.close()
    db.close()        

parseResults()