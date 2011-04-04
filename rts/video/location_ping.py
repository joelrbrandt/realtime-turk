from mod_python import apache, util
import simplejson as json
from datetime import datetime, timedelta

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

MIN_SECS_BETWEEN_PHASES = 2

PHASE_MAX_AGE_IN_MINUTES = 2
MAX_TIME_TO_WAIT_ALONE_IN_SECS = 10

def locationPing(request):
    request.content_type = "application/json"
    
    db = DBConnection()

    (phase, assignment, location, video_id) = getArgs(request)    
    servertime = unixtime(datetime.now())
    logging.debug("Location %s for video %s on phase %s" % (location, video_id, phase))
    
    cur_phase = getMostRecentPhase(video_id, db)    
    # Ensure that there isn't already a newer phase that
    # we should be returning to the client
    if cur_phase['phase'] == phase:
        # Now we know that we are on the right phase
        
        # Record where we are
        pushLocation(location, phase, assignment, video_id, servertime, db)
        
        # Has the phase already converged? (i.e., too small to be divisible)
        if phaseIsDivisible(cur_phase):
            (is_new_phase, new_min, new_max) = compareLocations(cur_phase, servertime, db)        
            if is_new_phase:
                # Agreement! Create a new phase.
                new_phase = createPhase(video_id, new_min, new_max, 
                                        servertime, db)
                if not phaseIsDivisible(new_phase):                                        
                    logging.debug("Picture has converged!")
                    closePhase(new_phase['phase'], servertime, False, db)
                    takePicture(new_phase, video_id, db)                                        
                                        
                request.write(json.dumps(new_phase, use_decimal=True))
                return

    # No reason to have a new phase; write the current phase back out
    request.write(json.dumps(cur_phase, use_decimal=True))
    
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
    Returns the most recent phase created for this video, or None
    if there are no such phases yet, or None if all the phases are too old
    """

    two_minutes_ago = datetime.now() - timedelta(minutes = PHASE_MAX_AGE_IN_MINUTES)
    
    sql = """SELECT phase, max, min, start, videoid FROM phases WHERE videoid = %s 
    AND start >= %s ORDER BY start DESC LIMIT 1"""
    
    result = db.query_and_return_array(sql, (video_id, unixtime(two_minutes_ago) ))
    
    if len(result) > 0:
        return result[0]
    else:
        # No phases for this video yet, create a first one
        return createPhase( video_id, 0.0, 1.0, unixtime(datetime.now()), db)


def closePhase(phase_id, servertime, is_abandoned, db):
    """ Closes a phase in the database by setting its end time to servertime """
    
    sql = """UPDATE phases SET end = %s, is_abandoned = %s WHERE phase = %s """
    db.query_and_return_array(sql, (servertime, is_abandoned, phase_id) )
    
        
def createPhase(video_id, new_min, new_max, servertime, db):
    """
    Creates a new phase for the video with the specified min and max
    """

    # First, close the old phase    
    most_recent = db.query_and_return_array("""SELECT MAX(phase) FROM phases WHERE videoid = %s""", (video_id, ))
    if len(most_recent) > 0:
        closePhase(most_recent[0]['MAX(phase)'], servertime, False, db)
    
    sql = """INSERT INTO phases (videoid, min, max, start) 
    VALUES (%s, %s, %s, %s)"""
    id = db.query_and_return_insert_id(sql, (video_id, new_min, new_max, servertime) )
    return dict(phase = id, max = new_max, min = new_min, start = servertime,
                videoid = video_id)


def pushLocation(location, phase, assignment, video_id, servertime, db):
    """
    Adds the current location to the given phase
    """
    
    sql = """INSERT INTO locations (videoid, assignmentid, location, servertime, phase) VALUES (%s, %s, %s, %s, %s)"""
    
    db.query_and_return_array(sql, (video_id, assignment, location, servertime, phase))


def compareLocations(phase, servertime, db):
    """
    Gets all the locations for the current video and phase out of the DB,
    then compares them to see if we should start a new phase
    """
    
    # have to get the entire row containing the MAX(servertime), ugh ugly SQL.
    sql = """SELECT locations.location, most_recent.assignmentid FROM locations, 
            (SELECT MAX(servertime) AS maxtime, assignmentid, phase FROM locations WHERE phase = %s AND servertime >= %s GROUP BY assignmentid) AS most_recent
            WHERE most_recent.assignmentid = locations.assignmentid
            AND most_recent.maxtime = locations.servertime
            AND most_recent.phase = locations.phase"""
    result = db.query_and_return_array(sql, (phase['phase'], phase['start'] + MIN_SECS_BETWEEN_PHASES))
    locations = sorted([row['location'] for row in result])

    logging.debug("len(locations): " + str(len(locations)))
    
    if len(locations) == 0:
        # all locations are just too recent
        return (False, None, None)
    
    # has the user been waiting alone?
    num_workers = len(set([row['assignmentid'] for row in result]))
    phase_time =  servertime - float(phase['start']) # it's OK to convert Decimal-->float, very little precision in the Decimal
    if num_workers == 1 and phase_time > MAX_TIME_TO_WAIT_ALONE_IN_SECS:
        abandonPhase(phase, db)
        # forever alone :(
        logging.debug("User has been waiting alone too long. Going to use an old phase.")
        return compareToHistoricalPhase(phase, servertime, db)
    
    ranges = getAgreement(phase['min'], phase['max'], locations)    
    best = max(ranges, key = lambda k: k['agreement'])

    # How many workers must agree?
    required_workers = max(AGREEMENT_PERCENT * len(locations), AGREEMENT_MINIMUM)
    logging.debug("Required to agree: %s. Agreeing: %s" % (required_workers, best['agreement']))
    if best['agreement'] >= required_workers:
        # They agree! Time to start new phase.
        return (True, best['min'], best['max'])
    else:
        return (False, None, None)


def getAgreement(phase_min, phase_max, locations):
    """ Returns an array of ranges and number of agreeing workers"""
    
    # The effective range that workers must agree on
    agreement_range = AGREEMENT_RANGE * float(phase_max - phase_min)
    
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
        
        #logging.debug("All locations: " + str(locations))
        
        # We're going to do this the easy-to-code way since the list is
        # likely to be small: just filter the entire list dynamically each time
        agreeing_locations = sorted(filter( lambda x: x >= range['min'] and x <= range['max'], locations ))
        #logging.debug("Agreeing locations: " + str(agreeing_locations))
        range['agreement'] = len( agreeing_locations )
        logging.debug("Agreement %s in [%s, %s)" % (range['agreement'], range['min'], range['max']) )
        
        # set the effective max of the new range to be the largest item in the range
        range['max'] = agreeing_locations[-1]
        
        ranges.append(range)
    return ranges

        
def phaseIsDivisible(phase):
    """ Returns True if the phase is large enough that 
    it can still be subdivided. """
    return (phase['max'] - phase['min'] > 0)
    

def takePicture(phase, video_id, db):
    """ Records a picture in the pictures table, given a converged
    phase """
    if phaseIsDivisible(phase):    
        raise Exception("Divisible phrase sent to takePicture")
    
    sql = """INSERT INTO pictures (videoid, location) VALUES (%s, %s)"""
    db.query_and_return_array(sql, (video_id, phase['min']) )


def abandonPhase(phase, db):
    """ Marks a phrase as abandoned. In other news, ORMs are nice."""
    
    db.query_and_return_array("""UPDATE phases SET is_abandoned = 1
    WHERE phase = %s""", (phase['phase'], ) )
    

def compareToHistoricalPhase(phase, servertime, db):
    """ Uses an older phase to mimic other people when there
    is nobody else around for this user to play with """
    older_phase = getNextHistoricalPhase(phase, db)
    
    if older_phase is None:
        logging.info("For now we are going to just keep waiting; there are no historical phases to refer to.") 
        return (False, None, None)
    else:        
        logging.debug("Historical phase is phase %s" % older_phase['phase'])    
        # we should be able to call compareLocations on the older
        # phase and get the older result back, which we can use
        # to simulate what happened in the past
        logging.debug(compareLocations(older_phase, servertime, db))
        return compareLocations(older_phase, servertime, db)    


def getNextHistoricalPhase(phase, db):
    """ Finds a previously identical phase to this one """

    sql = """SELECT phase, min, max, start, videoid FROM phases 
            WHERE videoid = %s AND end IS NOT NULL 
            AND is_abandoned = FALSE
            AND min = %s AND max = %s LIMIT 1"""
    result = db.query_and_return_array(sql, (phase['videoid'], phase['min'], phase['max']))
    
    if len(result) == 0:
        return None
    else:
        return result[0]
    