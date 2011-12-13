from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection
from rtsutils.decimal_encoder import DecimalEncoder

from rts import rts_logging
import logging

from rtsutils.timeutils import unixtime
from datetime import datetime
import random

from rtsutils.mole_poster import getMolesNeedingWhacks, MIN_WHACKS_TO_DECIDE


""" Writes to the request whether we need this particular worker to attack a video right now"""
def is_ready(request):
    request.content_type = "application/json"
    db = DBConnection()
    
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value
    workerid = form['workerid'].value
    
    result = getMolesNeedingWhacks(db, workerid)
    
    if len(result) == 0:
        request.write(json.dumps( { 'is_ready' : False } ))
    else:
        # grab the most recent molewhack
        random.shuffle(result)
        mole = result[0]
        result = getAndAssignMole(mole, assignmentid, db)
        request.write(json.dumps(result, cls=DecimalEncoder))
    
def getAndAssignMole(mole, assignmentid, db):
    moleid = mole['pk']
    updateAssignment(assignmentid, moleid)
    
    logging.debug("Moles needing whacks: " + str(moleid))
    phase = getMostRecentPhase(moleid, db)
    position = getMoleOptions(phase, moleid, db)    
    return dict( moleid = moleid, phase = phase, moleposition = position, is_ready = True)

    
def updateAssignment(assignmentid, moleid):
    """ Updates the database to map this video onto the assignment """
    db = DBConnection()
    try:
        db.query_and_return_array("""UPDATE assignments SET moleid = %s WHERE assignmentid = %s""", (moleid, assignmentid) )
    except:
        logging.exception("Error updating assignments table to set moleid")

def getMoleOptions(cur_phase, moleid, db):
    position = db.query_and_return_array("""SELECT moleposition FROM moles WHERE pk = %s""", (moleid, ))[0]['moleposition']
    
    return position


def getMostRecentPhase(mole_id, db):
    phase = getPhaseForMole(mole_id, db)
    
    if phase is None:
        return createPhase( mole_id, unixtime(datetime.now()), db)
    else:
        return phase

def getPhaseForMole(moleid, db):
    sql = """SELECT MAX(pk) FROM phase_lists WHERE moleid = %s"""
    result = db.query_and_return_array(sql, (moleid, ))
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


def createPhaseList(moleid, db):
    """ Creates a phase list in the DB """
    id = db.query_and_return_insert_id("""INSERT INTO phase_lists (moleid) VALUES (%s)""", (moleid, ))
    return id
    
        
def createPhase(moleid, servertime, db, phase_list = None):
    """
    Creates a new phase for the video with the specified min and max
    """
    
    if phase_list is None:
        phase_list = createPhaseList(moleid, db)
    
    sql = """INSERT INTO phases (start, phase_list) 
    VALUES (%s, %s)"""
    id = db.query_and_return_insert_id(sql, (servertime, phase_list) )
    return getPhase(id, db)

def decideMole(phase_list, db):
    result =  db.query_and_return_array("""SELECT moleid, MAX(phases.pk) FROM phases, phase_lists WHERE phase_list = %s and phase_lists.pk = phases.phase_list""", (phase_list, ))[0]
    moleid = result['moleid']
    last_phase = result['MAX(phases.pk)']
    
    whacks = db.query_and_return_array("""SELECT response, COUNT(*) FROM responses WHERE phaseid = %s ORDER BY COUNT(*) DESC""", (last_phase, ))
    
    logging.debug("Whacks: %s" % whacks)
    winner = whacks[0]['response']
    db.query_and_return_array("""INSERT INTO whack_decisions (moleid, phase_list, winnerid) VALUES (%s, %s, %s)""", (moleid, phase_list, winner) )
    

def getMoleForAssignment(assignmentid, db):
    result = db.query_and_return_array("""SELECT moleid FROM assignments WHERE assignmentid = %s""", (assignmentid, ) )
    return result[0]['moleid']
