import MySQLdb
from timeutils import unixtime
from datetime import datetime, timedelta
import simplejson as json
from timeutils import parseISO
import numpy
import settings
from padnums import pprint_table
import sys

EXPERIMENT = 21

def parseResults():      
    # get all the clicks
    assignments = getAssignments(EXPERIMENT)
    assignments.sort(key=lambda k: k['answer_time']['server'])  # we want them in completion order
    
    """ Now we look at each assignment and look at time diffs """
    printAssignments(assignments)
    
    print("\n\nworker logs")
    printWorkerLogs(assignments)

def getAssignments(experiment):
    """ Queries the database for all the assignments completed in this experiment, and populates the array with all relevant timestamps """
    
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE,
 use_unicode=True)
    cur = db.cursor()    
    
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
                                
    cur.close()
    db.close()                        

    return assignments

def printAssignments(assignments):
    """ Calculates relevant deltas and prints them out to the console """

    table = [["workerId", "assignmentId", "accept-show", "show-go", "go-answer"]]
    for click in assignments:
        answer_delta_go = total_seconds(click['answer_time']['client'] - click['go_time']['client'])
        go_delta_show = total_seconds(click['go_time']['client'] - click['show_time']['client'])
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

        answer_delta_go = total_seconds(click['answer_time']['client'] - click['go_time']['client'])
        worker_lags[click['workerid']].append(answer_delta_go)
        
    for workerid in worker_lags.keys():
        print(workerid + ' ' + str(worker_lags[workerid]))


def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0

parseResults()
