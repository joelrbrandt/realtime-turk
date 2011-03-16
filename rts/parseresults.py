import MySQLdb
from timeutils import unixtime
from datetime import datetime, timedelta
import simplejson as json
from timeutils import parseISO
import numpy
from scipy import stats
import settings
from padnums import pprint_table
import sys

EXPERIMENT = 25

class Assignment:
    """ Encapsulates information about an assignment completion """
    answer_time = None
    accept_time = None
    show_time = None
    go_time = None
    
    workerid = None
    assignmentid = None
    detail = None
    
    def answerDeltaGo(self):
        """ Time between clicking Go and clicking the first answer """
        if self.answer_time is not None and self.go_time is not None:
            return total_seconds(self.answer_time['client'] - self.go_time['client'])
        else:
            return None         
            
    def goDeltaShow(self):
        """ Time between the Go button showing up, and it being clicked """
        if self.go_time is not None and self.show_time is not None:            
            return total_seconds(self.go_time['client'] - self.show_time['client'])
        else:
            return None
    
    def showDeltaAccept(self):
        """ Time between accepting the task and the Go button appearing """
        if self.show_time is not None and self.accept_time is not None:
            return total_seconds(self.show_time['client'] - self.accept_time['client'])
        else:
            return None

def parseResults():      
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE,
 use_unicode=True)
    cur = db.cursor()   

    # get all the clicks
    assignments = getAssignments(cur, EXPERIMENT)
    assignments.sort(key=lambda k: k.answer_time['server'])  # we want them in completion order
    
    """ Now we look at each assignment and look at time diffs """
    printAssignments(sorted(assignments, key=lambda k: k.workerid))
    
    print("\n\n")
    printSummary(assignments)
    
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
        assignment = Assignment()
        assignment.workerid = row[1]
        assignment.assignmentid = row[3]
        assignment.detail = json.loads(row[2])
        
        assignment.answer_time = { 'client': datetime.fromtimestamp(row[0]),
                        'server': datetime.fromtimestamp(row[4]) }
        
        # when did the worker accept that task?
        cur.execute("""SELECT time, servertime from logging WHERE event='accept' AND assignmentid = '%s'""" % ( row[3] ))
        result = cur.fetchone()
        if result is not None:
            assignment.accept_time = { 'client': datetime.fromtimestamp(result[0]),
                            'server': datetime.fromtimestamp(result[1]) }
            
        # when did the task or 'go' button appear to the user?

        assignment.show_time = { 'client': datetime.fromtimestamp(parseISO(assignment.detail['showTime'])) } # no server time
            
        # when did the worker click the "go" button?
        cur.execute("""SELECT time, servertime from logging WHERE event='go' AND assignmentid = '%s'""" % ( row[3] ))
        result = cur.fetchone()
        if result is not None:
            assignment.go_time = { 'client': datetime.fromtimestamp(result[0]),
                        'server': datetime.fromtimestamp(result[1]) }
        
            
        assignments.append(assignment)

    return assignments

def printAssignments(assignments):
    """ Calculates relevant deltas and prints them out to the console """

    table = [["workerId", "assignmentId", "accept-show", "show-go", "go-answer"]]
    for click in assignments:     
        table.append( [ click.workerid, click.assignmentid, str(click.showDeltaAccept()), str(click.goDeltaShow()), str(click.answerDeltaGo()) ] )
        
    pprint_table(sys.stdout, table)


def printWorkerLogs(assignments):
    """ groups all logs by workerId and prints out performance for that worker """
    
    worker_lags = dict()
    # looking at per-user lag time
    for click in assignments:
        if not worker_lags.has_key(click.workerid):
            worker_lags[click.workerid] = []

        worker_lags[click.workerid].append(click.answerDeltaGo())
        
    for workerid in worker_lags.keys():
        print(workerid + ' ' + str(worker_lags[workerid]))

def printCurrentlyActiveCount(cur, experiment):
    ping_floor = datetime.now() - timedelta(seconds = 15)

    cur.execute("""SELECT COUNT(DISTINCT assignmentid) FROM logging WHERE event='ping' AND experiment = '%s' AND servertime >= %s""" % ( experiment, unixtime(ping_floor) ))
    result = cur.fetchone()[0]
    print("unique assignmentId pings in last 15 seconds: " + str(result))
    
def printSummary(assignments):
    print("WARNING: not removing first worker attempt to smooth")
    print("N = %d, %d unique workers" % (len(assignments), len(set([assignment.workerid for assignment in assignments]))))
    
    table = [["metric", "10%", "25%", "50%", "75%", "mean", "std. dev"]]
    accept_show = [click.showDeltaAccept() for click in assignments if click.showDeltaAccept() is not None]
    table.append( ["accept-show", 
                   str(stats.scoreatpercentile(accept_show, 10)),
                   str(stats.scoreatpercentile(accept_show, 25)),
                   str(stats.scoreatpercentile(accept_show, 50)),
                   str(stats.scoreatpercentile(accept_show, 75)),
                   str(numpy.mean(accept_show)),
                   str(numpy.std(accept_show)) ] )
    
    go_show = [click.goDeltaShow() for click in assignments if click.goDeltaShow() is not None]
    table.append( ["show-go",
                   str(stats.scoreatpercentile(go_show, 10)),
                   str(stats.scoreatpercentile(go_show, 25)),
                   str(stats.scoreatpercentile(go_show, 50)),
                   str(stats.scoreatpercentile(go_show, 75)),
                   str(numpy.mean(go_show)),
                   str(numpy.std(go_show)) ] )
    
    go_answer = [click.answerDeltaGo() for click in assignments if click.answerDeltaGo() is not None]
    table.append( ["go-answer",
                   str(stats.scoreatpercentile(go_answer, 10)),
                   str(stats.scoreatpercentile(go_answer, 25)),
                   str(stats.scoreatpercentile(go_answer, 50)),
                   str(stats.scoreatpercentile(go_answer, 75)),                   
                   str(numpy.mean(go_answer)),
                   str(numpy.std(go_answer)) ] )    
    
    pprint_table(sys.stdout, table)
    
     
def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0

parseResults()
