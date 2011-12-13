import work_approver

from db_connection import DBConnection

import logging

import sys
from optparse import OptionParser

import json
from decimal import Decimal

import settings

import datetime

from timeutils import parseISO

import mt_connection

APPROVE_REASON = "Thank you for whacking the mole!"
REJECT_REASON = "You did not click on the mole. Sorry."

BONUS_AMOUNT = 0.02
BONUS_REASON = "$0.02 bonus for quick response. Thank you!"
BONUS_TIME_LIMIT = Decimal(2) # seconds


"""
Mapping of answer dict keys (right) to meaning (left)

assignmentid = assignmentId
workerid = w
phases = p
accept = a
show = sh
go = g
donewaiting = dw
submit = su
"""

def answer_reviewer(answer):
    result = None
    approve_response = (True, APPROVE_REASON)
    reject_response = (False, REJECT_REASON)

    db = DBConnection()

    try:
        whacked = [int(s) for s in answer['m'].split('|')]
        assignmentid = answer['assignmentId']
        actualPosition = int(db.query_and_return_array("""SELECT moleposition FROM assignments, moles WHERE assignmentid = %s AND moles.pk = assignments.moleid""", (assignmentid, ))[0]['moleposition'])
        print("Whack! Position %s, goal position %s" % (whacked, actualPosition))

        if (actualPosition in whacked):
            result = approve_response
        else:
            result = reject_response
    except:
        logging.exception("error reviewing answer: " + str(answer))

    return result

def bonus_evaluator(answer):
    """ Returns tuple (True/False [give bonus?], Amount [float], Reason [string])"""

    bonus_response = (True, BONUS_AMOUNT, BONUS_REASON)
    no_bonus_response = (False, None, None)
    result = no_bonus_response
    
    try:
        workerid = answer['w']
        show = parseISO(answer['sh'])
        go = parseISO(answer['g'])
        diff = go-show
        if diff < BONUS_TIME_LIMIT:
            result = bonus_response
    except:
        logging.exception('error calculating bonus for answer: ' + str(answer))
    return result    

def approve_mole_hits_and_clean_up(verbose=True, dry_run=False):
    conn = mt_connection.get_mt_conn()
    print "== REVIEWING WHACKAMOLE HITS =="

    reviewed_counts = work_approver.review_pending_assignments(conn,
                                                               answer_reviewer=answer_reviewer,
                                                               bonus_evaluator= bonus_evaluator,
                                                               verbose=verbose,
                                                               dry_run=dry_run)
    
    print "\n\nDONE! Number of reviewed hits: " + str(reviewed_counts) + "\n\n"
    print "== CLEANING UP OLD HITS =="

    cleaned_counts = work_approver.clean_up_old_hits(conn, verbose=verbose, dry_run=dry_run)

    print "\n\nDONE! Number of cleaned hits: " + str(cleaned_counts) + "\n\n"
    return (reviewed_counts, cleaned_counts)
    
if __name__ == "__main__":
    approve_mole_hits_and_clean_up(verbose=True, dry_run=False)
