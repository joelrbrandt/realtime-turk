import MySQLdb
from timeutils import unixtime
from datetime import datetime, timedelta
import simplejson as json
from timeutils import parseISO
import numpy
import settings
from padnums import pprint_table
import sys

EXPERIMENT = 25

def parseResults():      
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE,
 use_unicode=True)
    cur = db.cursor()   

    # get all the clicks
    assignments = getAssignments(cur, EXPERIMENT)
    assignments.sort(key=lambda k: k['answer_time']['server'])  # we want them in completion order
    
    """ Now we look at each assignment and look at time diffs """
    printAssignments(sorted(assignments, key=lambda k: k['workerid']))
    
    print("\n\nworker logs")
    printWorkerLogs(assignments)
    
    print("\n\n")
    printCurrentlyActiveCount(cur, EXPERIMENT)
    
    cur.close()
    db.close()    

def getAssignments(cur, experiment):
    """ Queries the database for all the assignments completed in this experiment, and populates the array with all relevant timestamps """ 
    
    cur.execute("""SELECT MIN(time), workerid, detail, assignmentid, servertime from logging WHERE experiment = %s AND event='highlight' GROUP BY assignmentid""" % (experiment, ) )

    assignments = []

    """ For each assignment, get its completion information """
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
        
            
        assignments.append( {   'answer_time': answer_time,
                                'workerid': row[1],
                                'assignmentid': row[3],
                                'detail': json.loads(row[2]),
                                'accept_time': accept_time,
                                'show_time': show_time,
                                'go_time': go_time })

    return assignments

def printAssignments(assignments):
    """ Calculates relevant deltas and prints them out to the console """

    table = [["workerId", "assignmentId", "accept-show", "show-go", "go-answer"]]
    for click in assignments:
        answer_delta_go = go_delta_show = show_delta_accept = "None"
        
        if click['answer_time'] is not None and click['go_time'] is not None:
            answer_delta_go = total_seconds(click['answer_time']['client'] - click['go_time']['client'])
        if click['go_time']  is not None and click['show_time'] is not None:            
            go_delta_show = total_seconds(click['go_time']['client'] - click['show_time']['client'])
        if click['show_time'] is not None and click['accept_time']  is not None:
            show_delta_accept = total_seconds(click['show_time']['client'] - click['accept_time']['client'])
     
        table.append( [ click['workerid'], click['assignmentid'], str(show_delta_accept), str(go_delta_show), str(answer_delta_go) ] )
        
    out = sys.stdout
    pprint_table(out, table)


def printWorkerLogs(assignments):
    """ groups all logs by workerId and prints out performance for that worker """
    
    worker_lags = dict()
    # looking at per-user lag time
    for click in assignments:
        if not worker_lags.has_key(click['workerid']):
            worker_lags[click['workerid']] = []

        if click['answer_time'] is not None and click['go_time']  is not None:
            answer_delta_go = total_seconds(click['answer_time']['client'] - click['go_time']['client'])
        worker_lags[click['workerid']].append(answer_delta_go)
        
    for workerid in worker_lags.keys():
        print(workerid + ' ' + str(worker_lags[workerid]))

def printCurrentlyActiveCount(cur, experiment):
    ping_floor = datetime.now() - timedelta(seconds = 15)

    cur.execute("""SELECT COUNT(DISTINCT assignmentid) FROM logging WHERE event='ping' AND experiment = '%s' AND servertime >= %s""" % ( experiment, unixtime(ping_floor) ))
    result = cur.fetchone()[0]
    print("unique assignmentId pings in last 15 seconds: " + str(result))
    
def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0

parseResults()
