from boto.mturk import connection
import MySQLdb
import MySQLdb.cursors

import logging
import sys
from optparse import OptionParser

import settings
            
def get_mt_conn(sandbox=settings.SANDBOX):
    """
    returns a connection to mechanical turk.
    requires that settings defines the following variables:
    
    settings.SANDBOX:    True|False
    settings.aws_id:     your aws id
    settings.aws_secret: your aws secret key
    """
    if sandbox:
        host="mechanicalturk.sandbox.amazonaws.com"
    else:
        host="mechanicalturk.amazonaws.com"

    return connection.MTurkConnection(
        aws_access_key_id=settings.aws_id,
        aws_secret_access_key=settings.aws_secret,
        host=host)
    

def print_all_pending_answers():
    c = get_mt_conn()
    hits = c.get_reviewable_hits(page_size=100, sort_direction="Descending")
    for h in hits:
        print "HIT ID: " + h.HITId
        assignments = c.get_assignments(h.HITId)
        for a in assignments:
            print "  Assignment ID: " + a.AssignmentId
            print "  Status: " + a.AssignmentStatus
            print "  SubmitTime: " + a.SubmitTime
            print "  AutoApprovalTime: " + a.AutoApprovalTime
            for ans in a.answers:
                print "    Answer --"
                for q in ans:
                    print "      Question --"
                    print "        Answer: " + q.Answer
                    print "        FreeText: " + q.FreeText
                    print "        QuestionIdentifier: " + q.QuestionIdentifier

def approve_all_reviewable_assignments():
    c = get_mt_conn()
    hits = c.get_reviewable_hits(page_size=100, sort_direction="Descending")
    for h in hits:
        print "HIT ID: " + h.HITId
        assignments = c.get_assignments(h.HITId)
        for a in assignments:
            try:
                print "  Assignment ID: " + a.AssignmentId
                print "  Status: " + a.AssignmentStatus
                c.approve_assignment(a.AssignmentId)
                print "  SUCCESS!"
            except:
                print "  FAIL!"

                    

def dispose_all_hits():
    c = get_mt_conn()
    hits = c.get_reviewable_hits(page_size=100, sort_direction="Descending")
    for h in hits:
        try:
            c.dispose_hit(h.HITId)
            print "SUCCESS! Disposed HIT " + h.HITId
        except Exception, e:
            print "could not dispose HIT " + h.HITId + "\n" + str(e)

