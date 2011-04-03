from mod_python import apache, util
import json
from datetime import datetime

from rtsutils.db_connection import DBConnection
from rtsutils.timeutils import unixtime

from rts import rts_logging
import logging

# TODO: this stuff may need to go into transactions
# to avoid bugs

AGREEMENT_RANGE = .15   # Agreement must occur within this % 
                        # of the current phase range
AGREEMENT_PERCENT = (1.0 / 3) # This % of workers must agree on a range
AGREEMENT_MINIMUM = 2   # At least this many must agree (no single person!)

def locationPing(request):
    db = DBConnection()

    (phase, assignment, location, video_id) = getArgs(request)    
    servertime = unixtime(datetime.now())
    logging.debug("Location %s for video %s" % (location, video_id))
    
    cur_phase = getMostRecentPhase(video_id, db)
    if cur_phase['phase'] != phase:
        # There is a newer phase than the one we're looking at,
        # use that one instead and return to the client
        request.write(json.dumps(cur_phase))
        return
    
    # Now we know that we are on the right phase
    pushLocation(location, phase, assignment, video_id, servertime, db)
    (is_new_phase, new_min, new_max) = compareLocations(cur_phase, db)
    
    if is_new_phase:
        # Agreement! Create a new phase.
        id = createPhase(video_id, new_min, new_max, servertime, db)
        result = dict(phase=id, min=new_min, max=new_max)
        request.write(json.dumps(result))
    else:
        # Nobody agrees yet, return the current phase
        request.write(json.dumps(cur_phase))
    
def getArgs(request):
    """ 
    Gets the useful arguments out of the request object
    and parses them into a tuple
    """
    form = util.FieldStorage(request)    
    phase = int(form['phase'].value)
    assignment = form['assignmentid'].value
    location = float(form['location'].value)
    video_id = int(form['videoid'].value)
    
    return (phase, assignment, location, video_id)

    
def getMostRecentPhase(video_id, db):
    """
    Returns the most recent phase created for this video.
    Assumes that there is always at least one phase for this video.
    (Should have been created in ready.py)
    """
    
    sql = """SELECT phase, max, min FROM phases WHERE videoid = %s ORDER BY start DESC LIMIT 1"""
    
    return db.query_and_return_array(sql, (video_id,) )[0]

        
def createPhase(video_id, new_min, new_max, servertime, db):
    """
    Creates a new phase for the video with the specified min and max
    """

    # First, close the old phase    
    most_recent = db.query_and_return_array("""SELECT MAX(phase) FROM phases WHERE videoid = %s""", (video_id, ))
    if len(most_recent) > 0:
        sql = """UPDATE phases SET end = %s WHERE phase = %s """
        db.query_and_return_array(sql, (servertime, most_recent[0]['MAX(phase)']) )
    
    sql = """INSERT INTO phases (videoid, min, max, start) 
    VALUES (%s, %s, %s, %s)"""
    id = db.query_and_return_insert_id(sql, (video_id, new_min, new_max, servertime) )
    return id


def pushLocation(location, phase, assignment, video_id, servertime, db):
    """
    Adds the current location to the given phase
    """
    
    sql = """INSERT INTO locations (videoid, assignmentid, location, servertime, phase) VALUES (%s, %s, %s, %s, %s)"""
    
    db.query_and_return_array(sql, (video_id, assignment, location, servertime, phase))


def compareLocations(phase, db):
    """
    Gets all the locations for the current video and phase out of the DB,
    then compares them to see if we should start a new phase
    """
    
    sql = """SELECT location, MAX(servertime) FROM locations WHERE phase = %s GROUP BY assignmentid"""
    result = db.query_and_return_array(sql, (phase['phase'],))
    locations = sorted([row['location'] for row in result])
    
    # The effective range that workers must agree on
    agreement_range = max(AGREEMENT_RANGE * float(phase['max'] - phase['min']), 1)
    
    # We need to find out if at least required_workers have agreed on
    # a range that is at most agreement_range
    
    # We use a sliding window approach. Iterate through each location, then look
    # ahead to see how many locations are in the next agreement_rage positions.
    # Keep the range with the most agreeing people
    ranges = []
    for (i, location) in enumerate(locations):
        range = dict()
        
        range['min'] = location
        range['max'] = location + agreement_range
        # We're going to do this the easy-to-code way since the list is
        # likely to be small: just filter the entire list dynamically each time
        range['agreement'] = len( filter( lambda x: x >= range['min'] and x < range['max'], locations ) )
        logging.debug("Agreement %s in [%s, %s)" % (range['agreement'], range['min'], range['max']) )
        
        # set the effective max of the new range to be the largest item in the range
        range['max'] = locations[i + (range['agreement'] - 1)]
        
        ranges.append(range)
    
    best = max(ranges, key = lambda k: k['agreement'])

    # How many workers must agree
    required_workers = max(AGREEMENT_PERCENT * len(locations), AGREEMENT_MINIMUM)
    logging.debug("Required to agree: %s. Agreeing: %s" % (required_workers, best['agreement']))
    if best['agreement'] >= required_workers:
        # They agree! Time to start new phase.
        return (True, best['min'], best['max'])
    else:
        return (False, None, None)
        
    