import work_approver

from db_connection import DBConnection

import logging

import sys
from optparse import OptionParser

import simplejson as json

import settings

import datetime

from timeutils import parseISO

import mt_connection

MINIMUM_ACCURACY = 1;
APPROVE_REASON = "Accurate work. Thank you!"
REJECT_REASON = "You did not choose enough meaningful or good-looking photos. Sorry."
#BONUS_AMOUNT = 0.02
#BONUS_REASON = "$0.02 bonus for quick response. Thank you!"
#BONUS_TIME_LIMIT = 2.0 # seconds

"""
Mapping of answer dict keys (right) to meaning (left)

assignmentid = assignmentId
workerid = w
framearray = fa
accept = a
show = sh
go = g
submit = su
"""

def answer_reviewer(answer):
    result = None
    approve_response = (True, APPROVE_REASON)
    reject_response = (False, REJECT_REASON)
    print(answer)

    try:
        frames = json.loads(answer['fa'])
        enough_pictures = len(frames) >= 3
        print "enough pictures?: " + str(enough_pictures)
        if enough_pictures:
            result = approve_response
        else:
            result = reject_response
    except:
        logging.exception("error reviewing answer: " + str(answer))

    return result

def approve_video_hits_and_clean_up(verbose=True, dry_run=False):
    conn = mt_connection.get_mt_conn()
    print "== REVIEWING VIDEO HITS =="

    reviewed_counts = work_approver.review_pending_assignments(conn,
                                                               answer_reviewer=answer_reviewer,
                                                               verbose=verbose,
                                                               dry_run=dry_run)
    
    print "\n\nDONE! Number of reviewed hits: " + str(reviewed_counts) + "\n\n"
    print "== CLEANING UP OLD HITS =="

    cleaned_counts = work_approver.clean_up_old_hits(conn, verbose=verbose, dry_run=dry_run)

    print "\n\nDONE! Number of cleaned hits: " + str(cleaned_counts) + "\n\n"
    return (reviewed_counts, cleaned_counts)
    
if __name__ == "__main__":
    approve_video_hits_and_clean_up(verbose=True, dry_run=False)
