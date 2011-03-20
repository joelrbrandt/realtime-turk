from boto.mturk import connection

import logging

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


def print_assignment_details(a, indent=""):
    print indent + "Status: " + a.AssignmentStatus
    print indent + "SubmitTime: " + a.SubmitTime
    print indent + "AutoApprovalTime: " + a.AutoApprovalTime
    print indent + "Answer: " + str(reformat_external_question_answer(a.answers))

def reformat_external_question_answer(answer_array):
    """
    reformats an answer array from an External Question into a dict
    Note: if there are repeated element names in the answer array, the last value will be used
    """
    a = {}
    for ans in answer_array:
        for q in ans:
            a[q.QuestionIdentifier] = q.FreeText
    return a


def review_assignment(conn,
                      assignment,
                      answer_reviewer=lambda x: (True, None), 
                      bonus_evaluator=lambda x: (False, None, None),
                      verbose=True,
                      indent=""):
    """
    reviews passed in assignment using the functions passed in

    returns True if the assignment was successfully reviewed (assigned either 
      'approved' or 'rejected', or False otherwise
    
    conn:
      a mechanical turk connection

    assignment:
      the assignment to review

    answer_reviewer:
      a function that takes an answer dict and returns either the tuple
        (approved[True|False], "approval message" or None)
      or 'None' if it does not know how to review

    bonus_evaluator:
      a function that takes an answer dict and returns a tuple
        (bonused[True|False], bonus amount or None, "bonus message" or None)
      This function will only be called if answer_reviewer approved the answer
      To grant a bonus, both bonus amount and bonus message must be given

    verbose:
      print out details about the assignment when processing

    indent: 
      a string to indent each line of output by
    """
    result = False

    print indent + "Assignment ID: " + assignment.AssignmentId
    if verbose:
        print_assignment_details(assignment, indent=indent)
    parsed_answers = reformat_external_question_answer(assignment.answers)

    review = answer_reviewer(parsed_answers)
    if review == None: # chose not to review this assignment
        print indent + "ASSIGNMENT SKIPPED"
    else:
        result = True
        (approved, msg) = review

        if approved:
            conn.approve_assignment(assignment.AssignmentId, msg)
            if msg:
                print indent + "ASSIGNMENT APPROVED " + msg
            else:
                print indent + "ASSIGNMENT APPROVED"
            (bonused, amount, bonusmsg) = bonus_evaluator(parsed_answers)
            if bonused and amount != None and msg != None:
                conn.grant_bonus(assignment.WorkerId, 
                              assignment.AssignmentId, 
                              conn.get_price_as_price(amount),
                              bonusmsg)
                print indent + "ASSIGNMENT BONUSED: " + str(amount) + " " + str(msg)
            else:
                print indent + "NO BONUS"
        else:
            conn.reject_assignment(assignment.AssignmentId, msg)
            if msg:
                print indent + "ASSIGNMENT REJECTED " + msg
            else:
                print indent + "ASSIGNMENT REJECTED"


    return result

    
def review_pending_assignments(conn,
                               answer_reviewer=lambda x: (True, None), 
                               bonus_evaluator=lambda x: (False, None, None),
                               verbose=True):
    """
    reviews all pending assignments, calling "review assignment" for each
    
    returns number of assignments successfully reviewed

    See documentation for "review_assignment" for description of parameters
    """

    count = 0

    hits = conn.get_reviewable_hits(page_size=100, sort_direction="Descending")
    for h in hits:
        print "HIT ID: " + h.HITId
        assignments = conn.get_assignments(h.HITId, status="Submitted")
        for a in assignments:
            result = review_assignment(conn, a, 
                                       answer_reviewer=answer_reviewer, 
                                       bonus_evaluator=bonus_evaluator,
                                       verbose=verbose, indent="  ")
            if result:
                count += 1
    return count
        

def print_all_pending_answers(conn):
    hits = conn.get_reviewable_hits(page_size=100, sort_direction="Descending")
    for h in hits:
        print "HIT ID: " + h.HITId
        assignments = conn.get_assignments(h.HITId, status="Submitted")
        for a in assignments:
            print "  Assignment ID: " + a.AssignmentId
            print_assignment_details(a, indent="  ")

def autoapprove_all_reviewable_assignments(conn, verbose=True):
    return review_pending_assignments(conn, 
                                      answer_reviewer=lambda x: (True, None),
                                      bonus_evaluator=lambda x: (False, None, None),
                                      verbose=verbose)
                    
def delete_all_hits(conn, do_you_mean_it="NO"):
    if do_you_mean_it != "YES_I_MEAN_IT":
        print """
This will delete everything in your mechanical turk account
and autoapprove everything that hasn't been approved
if you realy mean it, run:

    dispose_all_hits(conn, do_you_mean_it='YES_I_MEAN_IT')
"""
        return 0

    else:
        count = 0
        try:
            hits = conn.search_hits(page_size=100)
            while len(hits) > 0:
                for h in hits:
                    try:
                        if h.HITStatus == "Reviewable":
                            # have to approve all, then call dispose_hit
                            print "Reviewing HIT " + h.HITId

                            assignments = conn.get_assignments(h.HITId, status="Submitted")
                            while len(assignments) > 0:
                                for a in assignments:
                                    print "Approving Assignment " + a.AssignmentId
                                    conn.approve_assignment(a.AssignmentId)
                                assignments = conn.get_reviewable_hits(h.HITId)                                

                            print "Assignments approved, Disposing HIT " + h.HITId
                            conn.dispose_hit(h.HITId)

                        else: # can call disable hit
                            print "Disabling HIT " + h.HITId
                            conn.disable_hit(h.HITId)

                        count += 1
                        print "SUCCESS! THE HIT IS GONE!"
                    except Exception, e:
                        print "ERROR DELETING HIT " + h.HITId + "\n" + str(e)

                hits = conn.search_hits(page_size=100)

        except Exception, e:
                print "Big error: \n" + str(e)

        print "ALL DONE! Deleted " + str(count) + " HITs"

        return count
