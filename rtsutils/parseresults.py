import settings
from rtsutils import condition
from rtsutils.word_clicker_approver import RECALL_LIMIT, PRECISION_LIMIT

from db_connection import DBConnection
from datetime import datetime, timedelta
import simplejson as json
from rtsutils.timeutils import *

import copy

import numpy
from scipy import stats, interpolate
from matplotlib import pyplot
import scikits.statsmodels
from matplotlib.font_manager import FontProperties

from padnums import pprint_table
import sys
from itertools import groupby

ITEM_OF_INTEREST = "design" #'waitbucket'

if ITEM_OF_INTEREST == "waitbucket":
    EXPERIMENTS = range(50, 56)
    settings.DB_DATABASE = 'wordclicker'
if ITEM_OF_INTEREST == "design":
    EXPERIMENTS = range(72, 76)
    settings.DB_DATABASE = 'wordclicker'

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
    all_assignments = getAssignments(EXPERIMENTS)
    
    # this sort is NECESSARY for groupby:
    # http://docs.python.org/library/itertools.html#itertools.groupby
    all_assignments.sort(key=lambda k: k.wait_bucket)
    
    for time_bucket, iter_bucket_assignments in groupby(all_assignments, key=lambda k: k.wait_bucket):    
        bucket_assignments = list(iter_bucket_assignments)
        # filter out assignments with bad precision or recall
        
        assignments = filter(lambda x: x.submit_time is not None and x.precision >= PRECISION_LIMIT and x.recall >= RECALL_LIMIT, bucket_assignments)
        
        print("\n\n\n\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        print("Time bucket: " + str(time_bucket) + " seconds")
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")        
        assignments.sort(key=lambda k: k.answer_time)  # we want them in completion order
        
        #print("\n\nworker logs")
        #printWorkerLogs(assignments)    
        
        """ Now we look at each assignment and look at time diffs """
        # print("\n\nassignments")
        #printAssignments(sorted(assignments, key=lambda k: k.workerid))
        
        print("\n\n")
        printSummary(assignments, bucket_assignments)
        
        print("\n\n")
        printConditionSummaries(assignments, bucket_assignments)
        
    print("\n\n")
    printCurrentlyActiveCount(EXPERIMENTS)
    
    print("\n\n")
    printSummary(filter(lambda x: x.submit_time is not None and x.precision >= PRECISION_LIMIT and x.recall >= RECALL_LIMIT, all_assignments), bucket_assignments)
    
    completed = filter(lambda x: x.submit_time is not None, all_assignments)
    print("Number of assignments attempted: %s" % len(all_assignments) )
    print("Number of completed assignments: %s" % len(completed) )
    print("Number of filtered assignments: %s" % len(filter(lambda x: x.precision < PRECISION_LIMIT or x.recall < RECALL_LIMIT, completed)))
    

    if ITEM_OF_INTEREST == "waitbucket":
        keylambda = lambda x: x.wait_bucket
    elif ITEM_OF_INTEREST == "design":
        keylambda = lambda x: x.condition
    
    #raw_input("Just the good ones...")
    #graphCDF(filter(lambda x: x.submit_time is not None and x.precision >= PRECISION_LIMIT and x.recall >= RECALL_LIMIT, all_assignments), keylambda)
    
    raw_input("Ne'er submitters become infinite wait time...")
    submitter_assignments = [ translateAssignment(assignment, bounce_infinite=True, poor_quality_infinite = False) for assignment in all_assignments]
    
    if ITEM_OF_INTEREST == "waitbucket":
        legend="Retainer Time"
    elif ITEM_OF_INTEREST == "design":
        legend="Design"
    
    graphCDF(submitter_assignments, keylambda, rejected_assignments = filter(lambda x: x.submit_time is not datetime.max, submitter_assignments), legend=legend)
    
    #raw_input("Ne'er submitters AND bad quality become infinite...")
    #graphCDF( [ translateAssignment(assignment, bounce_infinite=True, poor_quality_infinite = True) for assignment in all_assignments], keylambda)    
    
def translateAssignment(assignment, bounce_infinite = True, poor_quality_infinite = False):
    fixed = copy.deepcopy(assignment)
    if bounce_infinite:
        if assignment.show_time is None:
            fixed.show_time = datetime.min
            fixed.go_time = datetime.max    
        elif assignment.go_time is None:
            fixed.go_time = datetime.max
        elif assignment.submit_time is None:
            raise Exception("somebody hit GO but never submitted")
    
    if poor_quality_infinite and assignment.precision < PRECISION_LIMIT and assignment.recall < RECALL_LIMIT:
        fixed.show_time = datetime.min
        fixed.go_time = datetime.max            
    
    return fixed
    
def getAssignments(experiments):
    """ Queries the database for all the assignments completed in this experiment, and populates the array with all relevant timestamps """ 

    db = DBConnection()    
    experimentString = ', '.join([str(experiment) for experiment in experiments])
    results = db.query_and_return_array("""SELECT * from assignments a, workers w, hits h WHERE experiment IN (""" + experimentString + """) AND a.workerid = w.workerid AND a.hitid = h.hitid """ )

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

    print("Total number of assignments: %s" % (len(assignments)))
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

def printCurrentlyActiveCount(experiments):
    ping_floor = datetime.now() - timedelta(seconds = 15)
    ping_types = ["ping-waiting", "ping-showing", "ping-working"]

    db = DBConnection()

    results = dict()
    experimentString = ', '.join([str(experiment) for experiment in experiments])    
    for ping_type in ping_types:
    
        row = db.query_and_return_array("""SELECT COUNT(DISTINCT assignmentid) FROM logging WHERE event='%s' AND experiment IN (%s) AND servertime >= %s""" % ( ping_type, experimentString, unixtime(ping_floor) ))[0]
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
    
    go_show = [click.goDeltaShow() for click in assignments_including_incomplete]
    for i in range(len(go_show)):
        if go_show[i] is None:
            go_show[i] = sys.maxint
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
    #(r, p_val) = stats.pearsonr(accept_show, go_show)
    #print("Correlation between accept-show and show-go: %f, p<%f" % (r, p_val))
    #(r_answer, p_val_answer) = stats.pearsonr(go_show, go_answer)    
    #print("Correlation between show-go and go-answer: %f, p<%f" % (r_answer, p_val_answer))
    
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
            experiments_string = ','.join([str(ex) for ex in EXPERIMENTS])
            result = db.query_and_return_array(""" SELECT COUNT(DISTINCT assignmentid) FROM logging WHERE event = 'tetris_row_clear' AND experiment IN (%s) """, (experiments_string, ) )[0]
            num_playing = result['COUNT(DISTINCT assignmentid)']
            print(str(num_playing) + " assignments out of " + str(len(assignments)) + " (" + str(float(num_playing) / len(assignments) * 100) + "%) cleared a row in Tetris ")

def groupAssignmentsByKey(assignments, key):
    """Splits all assignments into groups based on their condition (e.g., baseline, tetris). Returns a dict from condition to list of assignments"""
    group_assignments = dict()

    all_groups = set([key(assignment) for assignment in assignments])
    for group in all_groups:
        filtered_assignments = filter(lambda assignment: key(assignment) == group, assignments)
        group_assignments[group] = filtered_assignments
    
    return group_assignments
    
def printConditionSummaries(assignments, assignments_including_incomplete):
    condition_assignments = groupAssignmentsByKey(assignments, lambda x: x.condition)
    condition_incomplete_assignments = groupAssignmentsByKey(assignments_including_incomplete, lambda x: x.condition)
    for condition in condition_assignments.keys():
        filtered_assignments = condition_assignments[condition]
        filtered_incomplete = condition_incomplete_assignments[condition]
        print("\n" + condition + ":")
        printSummary(filtered_assignments, filtered_incomplete, condition)
    
# http://matplotlib.sourceforge.net/api/pyplot_api.html#matplotlib.pyplot.step    
def graphCDF(assignments, keylambda, rejected_assignments = [], xaxis = "Seconds", yaxis = "P(response within x seconds)", legend="Retainer Time"):
    rejected_ids = [rejected.assignmentid for rejected in rejected_assignments]
    
    try:    
        pyplot.clf()
        pyplot.hold(True)
        x = numpy.linspace(0, 4, num=1000)
    
        group_assignments = groupAssignmentsByKey(assignments, keylambda)
        if legend == "Design":
            groups = ['baseline', 'alert', 'tetris', 'reward']
        else:
            groups = sorted(group_assignments.keys())
        
        for group in groups:  
        
            go_show = [click.goDeltaShow() for click in group_assignments[group]]
            ecdf = scikits.statsmodels.tools.ECDF(go_show)
            y = ecdf(x) # plots y in the CDF for each input x
            
            legend_label = str(group)
            if legend == "Retainer Time":
                if group < 60:
                    legend_label += " seconds"
                else:
                    num_minutes = group / 60
                    legend_label = str(num_minutes) + " minute"
                    if num_minutes > 1:
                        legend_label += "s"
            elif legend == "Design":
                if group == "alert":
                    legend_label = "Alert"
                elif group == "baseline":
                    legend_label = "Baseline"
                elif group == "reward":
                    legend_label = "Reward"
                elif group == "tetris":
                    legend_label = "Game"
            
            color = ''
            if group == "alert" or group == 600:
                color = 'm'
            
            """ for later
            if len(rejected_assignments) > 0:
                group_assignments = [assignment.assignmentid for assignment in group_assignments[group]]
                #print(group_assignments)
                
                not_included = [assignment for assignment in group_assignments[group] if assignment.assignmentid not in rejected_ids]
                
                print('lllllll')
                print(not_included)
                total_bounce = float(len(not_included)) / len(group_assignments[group])
                #print(total_bounce)
                
                pyplot.axhline(y=total_bounce, xmin=0.95, xmax=1)
            """
            
            pyplot.step(x, y, color, label=legend_label, linewidth=2)            
    
        pyplot.legend(loc = 2, title=legend, prop = FontProperties(size=12))  # 2 = Upper Left http://matplotlib.sourceforge.net/users/plotting/legend.html#legend-location
        pyplot.axis( [0.0, 4.0, 0.0, 1.0] )
        pyplot.xlabel(xaxis)
        pyplot.ylabel(yaxis)
        pyplot.yticks( numpy.arange(0, 1, 0.1) )
        pyplot.grid(True, linewidth=1, alpha=0.2)
        pyplot.show()
    except Exception, e:
        print("Graphing exception: " + str(e))

if __name__ == "__main__":
    parseResults()
