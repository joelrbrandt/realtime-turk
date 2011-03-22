import work_approver

import MySQLdb

import logging
import sys
from optparse import OptionParser

import simplejson as json

import settings

import datetime

from timeutils import parseISO

import mt_connection

"""
TODOs:

- add "Dry run" options to doit and stuff that gets called by do it (in work_approver)
- change it so that the approve reason appends the bonus reason if they get a bonus (so it's more clear)
- add pagination support for getting ALL HITs
- add a main function
- test it more

"""


APPROVE_REASON = "Accurate work. Thank you!"
REJECT_REASON = "Too many missed/erroneously clicked verbs. Sorry."
BONUS_AMOUNT = 0.02
BONUS_REASON = "$0.02 bonus for quick response. Thank you!"

PRECISION_LIMIT = 0.66  # 2/3s of what was selected must be verbs
RECALL_LIMIT = 0.5  # must have gotten 1/2 of all verbs

BONUS_TIME_LIMIT = 2.0 # seconds

"""
Mapping of answer dict keys (right) to meaning (left)

assignmentid = assignmentId
workerid = w
experiment = e
textid = t
wordarray = wa
accept = a
show = sh
go = g
first = f
submit = su
"""

def answer_reviewer(answer):
    result = None
    approve_response = (True, APPROVE_REASON)
    reject_response = (False, REJECT_REASON)

    try:
        words = json.loads(answer['wa'])
        textid = answer['t']
        a = calculateAccuracy(textid, words)
        print "calculated precision recall of: " + str(a)
        precision = a['precision']
        recall = a['recall']
        if precision > PRECISION_LIMIT and recall > RECALL_LIMIT:
            result = approve_response
        else:
            result = reject_response
    except:
        logging.exception("error reviewing answer: " + str(answer))

    return result

def bonus_evaluator(answer):
    bonus_response = (True, BONUS_AMOUNT, BONUS_REASON)
    no_bonus_response = (False, None, None)
    result = no_bonus_response
    try:
        show = parseISO(answer['sh'])
        go = parseISO(answer['g'])
        diff = go-show
        if diff < BONUS_TIME_LIMIT:
            result = bonus_response
    except:
        logging.exception('error calculating bonus for answer: ' + str(answer))
    return result

def doit(verbose=True):
    c = mt_connection.get_mt_conn()
    work_approver.review_pending_assignments(c,
                                             answer_reviewer=answer_reviewer,
                                             bonus_evaluator=bonus_evaluator,
                                             verbose=verbose)

def calculateAccuracy(text_id, verbs):
    """ Looks up the ground truth in the database and calculates precision and recall. """
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor()
    
    cur.execute("""SELECT wordid FROM groundtruth WHERE textid = %s""", (text_id))
    ground_truth = [row[0] for row in cur.fetchall()]
    
    try:
        precision = float(len(set(verbs).intersection(ground_truth))) / len(verbs)
    except ZeroDivisionError:
        precision = 1 # otherwise we show an error that they "highlighted many verbs", which is weird if you haven't highlighted anything
    
    try:
        recall = float(len(set(verbs).intersection(ground_truth))) / len(ground_truth)
    except ZeroDivisionError:
        recall = 0
        
    return { 'precision': precision, 'recall': recall }
    
