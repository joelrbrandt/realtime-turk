import settings
from rts import condition
from rtsutils.word_clicker_approver import RECALL_LIMIT, PRECISION_LIMIT

from db_connection import DBConnection
from datetime import datetime, timedelta
import simplejson as json
from rtsutils.timeutils import *

import numpy
from scipy import stats, interpolate
from matplotlib import pyplot
import scikits.statsmodels

from padnums import pprint_table
import sys
from itertools import groupby

EXPERIMENT = 40

class Assignment:
    """ Encapsulates information about an assignment completion """
    answer_time = None
    accept_time = None
    show_time = None
    go_time = None
    submit_time = None
    
    workerid = None
    assignmentid = None
    #detail = None
    
    wait_bucket = None
    precision = None
    recall = None
    
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
    # get all the clicks
    all_assignments = getAssignments(EXPERIMENT)
    
    # this sort is NECESSARY for groupby:
    # http://docs.python.org/library/itertools.html#itertools.groupby
    all_assignments.sort(key=lambda k: k.wait_bucket)
    for time_bucket, iter_bucket_assignments in groupby(all_assignments, key=lambda k: k.wait_bucket):    
        bucket_assignments = list(iter_bucket_assignments)
        # filter out assignments with bad precision or recall
        assignments = filter(lambda x: x.submit_time is not None and x.precision >= PRECISION_LIMIT and x.recall >= RECALL_LIMIT, bucket_assignments)
        
        print("Time bucket: " + str(time_bucket) + " seconds")
        assignments.sort(key=lambda k: k.answer_time)  # we want them in completion order
        
        print("\n\nworker logs")
        printWorkerLogs(assignments)    
        
        """ Now we look at each assignment and look at time diffs """
        print("\n\nassignments")
        printAssignments(sorted(assignments, key=lambda k: k.workerid))
        
        print("\n\n")
        printSummary(assignments, bucket_assignments)
        
        print("\n\n")
        printConditionSummaries(assignments, bucket_assignments)
        
        print("\n\n")
        printCurrentlyActiveCount(EXPERIMENT)
        
        graphCDF(assignments)   

def getAssignments(experiment):
    """ Queries the database for all the assignments completed in this experiment, and populates the array with all relevant timestamps """ 

    db = DBConnection()    
    results = db.query_and_return_array("""SELECT * from assignments a, workers w, hits h WHERE experiment = %s AND a.workerid = w.workerid AND a.hitid = h.hitid """ % (experiment,) )

    assignments = []

    """ For each assignment, get its completion information """
    for row in results:
        assignment = Assignment()
        assignment.workerid = row['workerid']
        assignment.assignmentid = row['assignmentid']
        assignment.wait_bucket = row['waitbucket']
        
        assignment.precision = row['precision']
        assignment.recall = row['recall']
        assignment.condition = condition.getConditionName(bool(row['is_alert']), bool(row['is_reward']), bool(row['is_tetris']))
        
        if row['first'] is not None:
            assignment.answer_time = datetime.fromtimestamp(row['first'])
        
        # when did the worker accept that task?
        if row['accept'] is not None:
            assignment.accept_time = datetime.fromtimestamp(row['accept'])
        
        # when did the task or 'go' button appear to the user?
        if row['show'] is not None:
            assignment.show_time = datetime.fromtimestamp(row['show'])
            
        # when did the worker click the "go" button?
        if row['go'] is not None:
            assignment.go_time = datetime.fromtimestamp(row['go'])
            
        if row['submit'] is not None:
            assignment.submit_time = datetime.fromtimestamp(row['submit'])
            
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

def printCurrentlyActiveCount(experiment):
    ping_floor = datetime.now() - timedelta(seconds = 15)
    ping_types = ["ping-waiting", "ping-showing", "ping-working"]

    db = DBConnection()

    results = dict()
    for ping_type in ping_types:
        row = db.query_and_return_array("""SELECT COUNT(DISTINCT assignmentid) FROM logging WHERE event='%s' AND experiment = '%s' AND servertime >= %s""" % ( ping_type, experiment, unixtime(ping_floor) ))[0]
        results[ping_type] = row['COUNT(DISTINCT assignmentid)']

        print(ping_type + ": unique assignmentIds pings in last 15 seconds: " + str(results[ping_type]))
    return results
    
def printSummary(assignments, assignments_including_incomplete, condition = None):
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
    
    # bounce rate
    mortality = 1 - float(len(assignments)) / len(assignments_including_incomplete)
    print("Mortality Rate: " + str(mortality))
    
    # preview to accept ratio: we can look for a given HIT id
    # (which will only have one assignment) how many unique IPs previewed it
    # it's possible that lots of people previewed and wanted, but only one
    # was fast enough to grab it?
    
    if condition is not None:
        db = DBConnection()
        if condition == 'tetris':
            result = db.query_and_return_array(""" SELECT COUNT(DISTINCT assignmentid) FROM logging WHERE event = 'tetris_row_clear' AND experiment = %s """, (EXPERIMENT, ) )[0]
            num_playing = result['COUNT(DISTINCT assignmentid)']
            print(str(num_playing) + " assignments out of " + str(len(assignments)) + " (" + str(float(num_playing) / len(assignments) * 100) + "%) cleared a row in Tetris ")

def groupAssignmentsByCondition(assignments):
    """Splits all assignments into groups based on their condition (e.g., baseline, tetris). Returns a dict from condition to list of assignments"""
    condition_assignments = dict()

    all_conditions = set([assignment.condition for assignment in assignments])
    for condition in all_conditions:
        filtered_assignments = filter(lambda assignment: assignment.condition == condition, assignments)
        condition_assignments[condition] = filtered_assignments
    
    return condition_assignments
    
def printConditionSummaries(assignments, assignments_including_incomplete):
    condition_assignments = groupAssignmentsByCondition(assignments)
    for condition in condition_assignments.keys():
        filtered_assignments = condition_assignments[condition]
        print("\n" + condition + ":")
        printSummary(filtered_assignments, condition)
    
     
def total_seconds(td):
    return td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000.0
    
# http://matplotlib.sourceforge.net/api/pyplot_api.html#matplotlib.pyplot.step    
def graphCDF(assignments):
    pyplot.clf()
    pyplot.hold(True)
    x = numpy.linspace(0, 100, num=1000)

    condition_assignments = groupAssignmentsByCondition(assignments)
    for condition in condition_assignments.keys():
        go_show = [click.goDeltaShow() for click in condition_assignments[condition]]
        ecdf = scikits.statsmodels.tools.ECDF(go_show)
        y = ecdf(x) # plots y in the CDF for each input x
        
        pyplot.step(x, y, label=condition, linewidth=2)

    pyplot.legend()

if __name__ == "__main__":
    parseResults()
