from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection
from rtsutils.decimal_encoder import DecimalEncoder

from rts import rts_logging
import logging

from rtsutils.timeutils import unixtime
from datetime import datetime
import random

from rtsutils.ab_poster import getVotesNeedingOpinions, MIN_VOTES_TO_DECIDE


""" Writes to the request whether we need this particular worker to attack a video right now"""
def is_ready(request):
    request.content_type = "application/json"
    db = DBConnection()
    
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value
    workerid = form['workerid'].value
    
    result = getVotesNeedingOpinions(db, workerid)
    
    if len(result) == 0:
        request.write(json.dumps( { 'is_ready' : False } ))
    else:
        # grab the most recent video upload
        vote = result[0]
        result = getAndAssignVote(vote, assignmentid, db)
        request.write(json.dumps(result, cls=DecimalEncoder))
    
def getAndAssignVote(vote, assignmentid, db):
    voteid = vote['pk']
    updateAssignment(assignmentid, voteid)
    
    logging.debug("ABs needing votes: " + str(voteid))
    phase = getMostRecentPhase(voteid, db)
    photos = getABOptions(phase, voteid, db)    
    random.shuffle(photos)
    return dict( voteid = voteid, phase = phase, photos = photos, is_ready = True, question = vote['question'])

    
def updateAssignment(assignmentid, videoid):
    """ Updates the database to map this video onto the assignment """
    db = DBConnection()
    try:
        db.query_and_return_array("""UPDATE assignments SET voteid = %s WHERE assignmentid = %s""", (videoid, assignmentid) )
    except:
        logging.exception("Error updating assignments table to set videoid")

def getABOptions(cur_phase, voteid, db):
    options = db.query_and_return_array("""SELECT * FROM vote_options, phase_options WHERE phaseid = %s AND phase_options.optionid = vote_options.pk""", (cur_phase['pk'], ))
    
    if len(options) == 0:
        # no phases yet, get 'em all!
        options = db.query_and_return_array("""SELECT * FROM vote_options WHERE voteid = %s""", (voteid, ))
    
    return list(options)


def getMostRecentPhase(vote_id, db):
    phase = getPhaseForVote(vote_id, db)
    
    if phase is None:
        return createPhase( vote_id, unixtime(datetime.now()), db)
    else:
        return phase

def getPhaseForVote(voteid, db):
    sql = """SELECT MAX(pk) FROM phase_lists WHERE voteid = %s"""
    result = db.query_and_return_array(sql, (voteid, ))
    if len(result) == 0:
        return None # no phase list for that video exists, can't have any videos
    phase_list = result[0]['MAX(pk)']


    # get the most recent known phase    
    sql = """SELECT pk FROM phases WHERE phase_list = %s
            ORDER BY pk DESC LIMIT 1"""
    result = db.query_and_return_array(sql, (phase_list, ))
    if len(result) == 0:
        return None # no phase in that phase list
    else:
        return getPhase(result[0]['pk'], db)

def getPhase(phase_id, db):
    phase = db.query_and_return_array("""SELECT * FROM phases WHERE pk = %s""", (phase_id, ) )[0]    

    return phase

def closePhase(phase_id, servertime, db):
    """ Closes a phase in the database by setting its end time to servertime """
    logging.debug("closing phase %s" % (phase_id, ))
    
    sql = """UPDATE phases SET end = %s WHERE pk = %s """
    db.query_and_return_array(sql, (servertime, phase_id) )


def createPhaseList(voteid, db):
    """ Creates a phase list in the DB """
    id = db.query_and_return_insert_id("""INSERT INTO phase_lists (voteid) VALUES (%s)""", (voteid, ))
    return id
    
        
def createPhase(voteid, servertime, db, phase_list = None):
    """
    Creates a new phase for the video with the specified min and max
    """
    
    if phase_list is None:
        phase_list = createPhaseList(voteid, db)
    
    sql = """INSERT INTO phases (start, phase_list) 
    VALUES (%s, %s)"""
    id = db.query_and_return_insert_id(sql, (servertime, phase_list) )
    return getPhase(id, db)

def decideVote(phase_list, db):
    result =  db.query_and_return_array("""SELECT voteid, MAX(phases.pk) FROM phases, phase_lists WHERE phase_list = %s and phase_lists.pk = phases.phase_list""", (phase_list, ))[0]
    voteid = result['voteid']
    last_phase = result['MAX(phases.pk)']
    
    votes = db.query_and_return_array("""SELECT response, COUNT(*) FROM responses WHERE phaseid = %s ORDER BY COUNT(*) DESC""", (last_phase, ))
    
    logging.debug("Votes: %s" % votes)
    winner = votes[0]['response']
    db.query_and_return_array("""INSERT INTO vote_decisions (voteid, phase_list, winnerid) VALUES (%s, %s, %s)""", (voteid, phase_list, winner) )
    

def getVoteForAssignment(assignmentid, db):
    result = db.query_and_return_array("""SELECT voteid FROM assignments WHERE assignmentid = %s""", (assignmentid, ) )
    return result[0]['voteid']