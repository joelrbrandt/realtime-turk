import settings
from rts import condition

import MySQLdb
from datetime import datetime, timedelta
import simplejson as json
from rtsutils.timeutils import *
import numpy
from scipy import stats
from padnums import pprint_table
import sys

EXPERIMENT = 31

class Assignment:
    """ Encapsulates information about an assignment completion """
    answer_time = None
    accept_time = None
    show_time = None
    go_time = None
    
    workerid = None
    assignmentid = None
    #detail = None
    
    condition = None
    
    def answerDeltaGo(self):
        """ Time between clicking Go and clicking the first answer """
        if self.answer_time is not None and self.go_time is not None:
            return total_seconds(self.answer_time - self.go_time)
        else:
            return None         
            
    def goDeltaShow(self):
        """ Time between the Go button showing up, and it being clicked """
        if self.go_time is not None and self.show_time is not None:            
            return total_seconds(self.go_time - self.show_time)
        else:
            return None
    
    def showDeltaAccept(self):
        """ Time between accepting the task and the Go button appearing """
        if self.show_time is not None and self.accept_time is not None:
            return total_seconds(self.show_time - self.accept_time)
        else:
            return None

def parseResults():      
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE,
 use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)   

    # get all the clicks
    assignments = getAssignments(cur, EXPERIMENT)
    assignments.sort(key=lambda k: k.answer_time)  # we want them in completion order
    
    print("\n\nworker logs")
    printWorkerLogs(assignments)    
    
    """ Now we look at each assignment and look at time diffs """
    print("\n\nassignments")
    printAssignments(sorted(assignments, key=lambda k: k.workerid))
    
    print("\n\n")
    printSummary(assignments)
    
    print("\n\n")
    printConditionSummaries(assignments)
    
    print("\n\n")
    printCurrentlyActiveCount(cur, EXPERIMENT)
    
    cur.close()
    db.close()    

def getAssignments(cur, experiment):
    """ Queries the database for all the assignments completed in this experiment, and populates the array with all relevant timestamps """ 
    
    cur.execute("""SELECT * from submissions sub, workers w WHERE experiment = %s AND sub.workerid = w.workerid""" % (experiment, ) )

    assignments = []

    """ For each assignment, get its completion information """
    for row in cur.fetchall():
        assignment = Assignment()
        assignment.workerid = row['workerid']
        assignment.assignmentid = row['assignmentid']
        assignment.condition = condition.getConditionName(bool(row['is_alert']), bool(row['is_reward']), bool(row['is_tetris']))
        
        assignment.answer_time = datetime.fromtimestamp(row['first'])
        
        # when did the worker accept that task?
        assignment.accept_time = datetime.fromtimestamp(row['accept'])
        
        # when did the task or 'go' button appear to the user?
        assignment.show_time = datetime.fromtimestamp(row['show'])
            
        # when did the worker click the "go" button?
        assignment.go_time = datetime.fromtimestamp(row['go'])
            
        assignments.append(assignment)

    return assignments

def printAssignments(assignments):
    """ Calculates relevant deltas and prints them out to the console """

    table = [["workerId", "condition", "assignmentId", "accept-show", "show-go", "go-answer"]]
    for click in assignments:     
        table.append( [ click.workerid, click.condition, click.assignmentid, str(click.showDeltaAccept()), str(click.goDeltaShow()), str(click.answerDeltaGo()) ] )
        
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
    result = cur.fetchone()['COUNT(DISTINCT assignmentid)']
    print("unique assignmentId pings in last 15 seconds: " + str(result))
    return result
    
def printSummary(assignments):
    # TODO?: WARNING: not removing first worker attempt to smooth
    print("N = %d, %d unique workers" % (len(assignments), len(set([assignment.workerid for assignment in assignments]))))
    
    if len(assignments) == 0:
        return
    
    table = [["metric", "10%", "25%", "50%", "75%", "90%", "mean", "std. dev"]]
    accept_show = [click.showDeltaAccept() for click in assignments if click.showDeltaAccept() is not None]
    table.append( ["accept-show", 
                   str(stats.scoreatpercentile(accept_show, 10)),
                   str(stats.scoreatpercentile(accept_show, 25)),
                   str(stats.scoreatpercentile(accept_show, 50)),
                   str(stats.scoreatpercentile(accept_show, 75)),
                   str(stats.scoreatpercentile(accept_show, 90)),                   
                   str(numpy.mean(accept_show)),
                   str(numpy.std(accept_show)) ] )
    
    go_show = [click.goDeltaShow() for click in assignments if click.goDeltaShow() is not None]
    table.append( ["show-go",
                   str(stats.scoreatpercentile(go_show, 10)),
                   str(stats.scoreatpercentile(go_show, 25)),
                   str(stats.scoreatpercentile(go_show, 50)),
                   str(stats.scoreatpercentile(go_show, 75)),
                   str(stats.scoreatpercentile(go_show, 90)),                   
                   str(numpy.mean(go_show)),
                   str(numpy.std(go_show)) ] )
    
    go_answer = [click.answerDeltaGo() for click in assignments if click.answerDeltaGo() is not None]
    table.append( ["go-answer",
                   str(stats.scoreatpercentile(go_answer, 10)),
                   str(stats.scoreatpercentile(go_answer, 25)),
                   str(stats.scoreatpercentile(go_answer, 50)),
                   str(stats.scoreatpercentile(go_answer, 75)),                   
                   str(stats.scoreatpercentile(go_answer, 90)),                                      
                   str(numpy.mean(go_answer)),
                   str(numpy.std(go_answer)) ] )
    
    pprint_table(sys.stdout, table)
    
    # Correlation between wait-show and show-go
    (r, p_val) = stats.pearsonr(accept_show, go_show)
    print("Correlation between accept-show and show-go: %f, p<%f" % (r, p_val))
    (r_answer, p_val_answer) = stats.pearsonr(go_show, go_answer)    
    print("Correlation between show-go and go-answer: %f, p<%f" % (r_answer, p_val_answer))    
    
def printConditionSummaries(assignments):
    all_conditions = set([assignment.condition for assignment in assignments])
    for condition in all_conditions:
        filtered_assignments = filter(lambda assignment: assignment.condition == condition, assignments)
        print("\n" + condition + ":")
        printSummary(filtered_assignments)
    
     
def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0

if __name__ == "__main__":
    parseResults()