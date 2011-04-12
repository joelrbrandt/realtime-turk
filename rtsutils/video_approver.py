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

MINIMUM_ACCURACY = 1;
APPROVE_REASON = "Accurate work. Thank you!"
REJECT_REASON = "You did not agree with the other Turkers, and your extra question response was incorrect. Sorry."

BONUS_AMOUNT = 0.03
BONUS_REASON = "$0.03 bonus for quick response. Thank you!"
BONUS_TIME_LIMIT = Decimal(2) # seconds


"""
Mapping of answer dict keys (right) to meaning (left)

assignmentid = assignmentId
workerid = w
phases = p
accept = a
show = sh
go = g
submit = su
"""

def answer_reviewer(answer):
    result = None
    approve_response = (True, APPROVE_REASON)
    reject_response = (False, REJECT_REASON)

    try:
        phases = json.loads(answer['p'])
        locations = json.loads(answer['loc'])
        if answer['v'] != "":
            validation = answer['v']
        else:
            validation = None
        
        if agreedWithPhases(phases, locations, 1) or validationAgreed(validation):
            result = approve_response
        else:
            result = reject_response
    except:
        logging.exception("error reviewing answer: " + str(answer))

    return result

def agreedWithPhases(phases, locations, min_phases):
    count_agreed = 0
    
    db = DBConnection()
    
    for i in range(len(phases)-1):
        # get the location we were at when the phase ended
        last_location = Decimal(str(locations[i]))
        
        # get the bounds that ended up being decided on (e.g., the next phase)
        bounds = db.query_and_return_array("""SELECT min, max FROM phases WHERE phase = %s""", (phases[i+1], ))[0]
        
        if bounds['min'] <= last_location and last_location <= bounds['max']:
            count_agreed += 1
    
    return count_agreed >= min_phases
    
def validationAgreed(chosen_image):
    db = DBConnection()
    good = getImages(db, True)
    print(good)
    print(chosen_image)
    
    return chosen_image in good
    
    
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

def approve_video_hits_and_clean_up(verbose=True, dry_run=False):
    conn = mt_connection.get_mt_conn()
    print "== REVIEWING VIDEO HITS =="

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


def getImages(db, is_good):
    images = db.query_and_return_array("""SELECT filename FROM verification WHERE is_good = %s""", (is_good, ))
    return [row['filename'] for row in images]

    
if __name__ == "__main__":
    approve_video_hits_and_clean_up(verbose=True, dry_run=False)
