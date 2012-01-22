import sys
if sys.modules.has_key('mod_python'):
    from mod_python import apache, util
import json
from datetime import datetime, timedelta

from rtsutils.db_connection import DBConnection
from rtsutils.timeutils import unixtime

from rts import rts_logging
import logging
from decimal import Decimal

# TODO: this stuff may need to go into transactions
# to avoid bugs

AGREEMENT_RANGE = Decimal(25) / Decimal(100)   # Agreement must occur within this % 
                        # of the current phase range
AGREEMENT_PERCENT = (1.0 / 3) # This % of workers must agree on a range
AGREEMENT_MINIMUM = 2   # At least this many must agree (no single person!)

HYSTERESIS_SECONDS = Decimal(str(3.0))

PHASE_MAX_AGE_IN_SECONDS = 30
MAX_TIME_TO_WAIT_ALONE_IN_SECS = 10

# worker must have seen at least this % of the available area
MINIMUM_RANGE_EXPLORATION = Decimal(1) / Decimal(10)

def locationPing(request):
    request.content_type = "application/json"
    
    db = DBConnection(autocommit = False)
    start = datetime.now()

    try:
        (phase, assignment, location, video_id) = getArgs(request)    
        servertime = unixtime(datetime.now())
        # logging.debug("Location %s for video %s on phase %s" % (location, video_id, phase))
        
        cur_phase = getMostRecentPhase(video_id, db)
        
        # Ensure that there isn't already a newer phase that
        # we should be returning to the client    
        if cur_phase['phase'] != phase:
            request.write(json.dumps(cur_phase, cls=DecimalEncoder))
        else:
            # Record where we are
            pushLocation(location, phase, assignment, video_id, servertime, db)
            
            # Has the phase already converged? (i.e., too small to be divisible)
            (is_new_phase, new_min, new_max) = compareLocations(cur_phase, servertime, db)        
            if is_new_phase:
                closePhase(cur_phase['phase'], servertime, False, db)
                # Agreement! Create a new phase.
                new_phase = createPhase(video_id, new_min, new_max, 
                                        servertime, cur_phase['phase_list'], db)
                logging.debug("Creating new phase: %s" % new_phase)
                if not phaseIsDivisible(new_phase):                                        
                    logging.debug("Picture has converged!")
                    closePhase(new_phase['phase'], servertime, False, db)
                    takePicture(new_phase, video_id, db)                                        
                                        
                request.write(json.dumps(new_phase, cls=DecimalEncoder))
            else:
                request.write(json.dumps(cur_phase, cls=DecimalEncoder))        
        db.commit()
        
    except Exception, e:
        db.rollback()
        logging.exception(e)
        raise
    
def getArgs(request):
    """ 
    Gets the useful arguments out of the request object
    and parses them into a tuple
    """
    form = util.FieldStorage(request)    
    phase = int(form['phase'].value)
    assignment = form['assignmentid'].value
    location = Decimal(form['location'].value)
    video_id = int(form['videoid'].value)
    
    return (phase, assignment, location, video_id)


def getMostRecentPhase(video_id, db, restart_if_converged = False):
    phase = getByVideo(video_id, db)
    
    # is there a phase ongoing?
    if phase is not None and not phase['is_abandoned'] and not (phase['end'] is not None and restart_if_converged):
        # if it's not a closed phase and we're forcing restart of converged phases (e.g., choosing a random video)
        
        # how old is this -- is it abandoned?
        sql = """SELECT servertime FROM locations WHERE
        phase = %s ORDER BY servertime DESC LIMIT 1"""
        time_result = db.query_and_return_array(sql, (phase['phase'], ))
        time_bound = unixtime(datetime.now() - 
                              timedelta(seconds = PHASE_MAX_AGE_IN_SECONDS))
        if phase['start'] > time_bound or (len(time_result) > 0 and time_result[0]['servertime'] > time_bound):
            # it's a recent, ongoing phase. return it.
            return phase
        else:
            # it's an old phase and we need to abandon it
            abandonPhase(phase['phase'], db)
        
    # if we got here, we need to create a new phase
    return createPhase( video_id, Decimal(0), Decimal(1), unixtime(datetime.now()), None, db)
    

def getPhase(phase_id, db):
    phase = db.query_and_return_array("""SELECT phases.phase, phases.min, phases.max, phases.start, phases.end, phases.is_abandoned, phases.phase_list, COUNT(DISTINCT assignmentid) AS numworkers FROM phases, locations WHERE locations.phase = phases.phase AND phases.phase = %s""", (phase_id, ) )[0]    

    return phase
    
def getByVideo(video_id, db):
    """
    Returns the most recent phase created for this video, or None
    if there are no such phases yet, or None if all the phases are too old
    """
    
    sql = """SELECT MAX(pk) FROM phase_lists WHERE videoid = %s"""
    result = db.query_and_return_array(sql, (video_id, ))
    if len(result) == 0:
        return None # no phase list for that video exists, can't have any videos
    phase_list = result[0]['MAX(pk)']

    # get the most recent known phase    
    sql = """SELECT phase FROM phases WHERE phase_list = %s
            ORDER BY phase DESC LIMIT 1"""
    result = db.query_and_return_array(sql, (phase_list, ))
    #logging.debug("most recent known phrase in phrase list %s: %s" % (phase_list, result))
    if len(result) == 0:
        return None # no phase in that phase list
    else:
        return getPhase(result[0]['phase'], db)


def abandonPhase(phase_id, db):
    """ Marks a phase as abandoned """
    logging.debug("Phase %s is abandoned" % phase_id)
    closePhase(phase_id, None, True, db)


def closePhase(phase_id, servertime, is_abandoned, db):
    """ Closes a phase in the database by setting its end time to servertime """
    logging.debug("closing phase %s" % (phase_id, ))
    
    sql = """UPDATE phases SET end = %s, is_abandoned = %s WHERE phase = %s """
    db.query_and_return_array(sql, (servertime, is_abandoned, phase_id) )


def createPhaseList(video_id, db):
    """ Creates a phase list in the DB """
    id = db.query_and_return_insert_id("""INSERT INTO phase_lists (videoid) VALUES (%s)""", (video_id, ))
    return id
    
        
def createPhase(video_id, new_min, new_max, servertime, phase_list, db):
    """
    Creates a new phase for the video with the specified min and max
    """
    
    if phase_list is None:
        phase_list = createPhaseList(video_id, db)
    
    sql = """INSERT INTO phases (min, max, start, phase_list) 
    VALUES (%s, %s, %s, %s)"""
    id = db.query_and_return_insert_id(sql, (new_min, new_max, servertime, phase_list) )
    return getPhase(id, db)


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
    
    time_floor = servertime - HYSTERESIS_SECONDS
    
    # get all the location pings in this phase in the last HYSTERESIS seconds,
    # but only those people who have actually been around for HYSTERESIS seconds
    # in the phase (we don't want to fire when someone just clicked the slider
    # for the first time
    sql = """SELECT locations.assignmentid, location, servertime,
             min_times.range_percent
             FROM locations, (
                SELECT assignmentid, locations.phase, 
                (MAX(location) - MIN(location) + 0.01)/(max - min + 0.01) AS range_percent 
                FROM locations, phases
                WHERE locations.phase = %s 
                AND locations.phase = phases.phase
                GROUP BY assignmentid                
            ) AS min_times WHERE locations.phase = min_times.phase AND min_times.assignmentid = locations.assignmentid AND servertime >= %s"""
    result = db.query_and_return_array(sql, (phase['phase'], time_floor ))
    #locations = sorted([row['location'] for row in result])

    if len(result) == 0:
        return (False, None, None)
    
    # has the user been waiting alone?
    num_workers = len(set([row['assignmentid'] for row in result]))
    if num_workers == 1:
        # get the earliest ping
        sql = """SELECT MIN(servertime) FROM locations WHERE
                 phase = %s AND assignmentid = %s"""
        earliest_ping = db.query_and_return_array(sql, (phase['phase'], result[0]['assignmentid']))[0]['MIN(servertime)']
        
        waiting_time = servertime - earliest_ping
        logging.debug("waiting time: %s " % waiting_time)
        if waiting_time > MAX_TIME_TO_WAIT_ALONE_IN_SECS:        
            # forever alone :(
            logging.debug("User has been waiting alone too long. Going to use an old phase.")
            return compareToHistoricalPhase(phase, servertime, db)
        else:
            # temporarily alone
            return (False, None, None)
    
    ranges = getAgreement(phase['min'], phase['max'], result)    
    best = max(ranges, key = lambda k: k['agreement'])

    # How many workers must agree?
    required_workers = max(AGREEMENT_PERCENT * num_workers, AGREEMENT_MINIMUM)
    #logging.debug("Required to agree: %s. Agreeing: %s" % (required_workers, best['agreement']))
    if best['agreement'] >= required_workers:
        # They agree! Time to start new phase.
        return (True, best['min'], best['max'])
    else:
        return (False, None, None)


def getAgreement(phase_min, phase_max, locations):
    """ Returns an array of ranges and number of agreeing workers"""
    
    # The effective range that workers must agree on
    agreement_range = AGREEMENT_RANGE * Decimal(phase_max - phase_min)
    #logging.debug("Agreement range: %s, phase range %s" % (agreement_range, phase_max - phase_min))
    
    # We need to find out if at least required_workers have agreed on
    # a range that is at most agreement_range
    
    locations_by_worker = groupByKey(locations, lambda x: x['assignmentid'])    
    logging.debug("How many locations? %s", (len(locations), ))
    
    # 
    ranges = []
    for (i, location) in enumerate(locations):
        range = dict()
        
        range['min'] = location['location']
        range['max'] = location['location'] + agreement_range
        range['agreement'] = 0
        
        farthest_right = range['min']
        for (assignmentid, assignment_locations) in locations_by_worker.items():
            only_in_range = filter( lambda x: 
                x['location'] >= range['min'] 
                and x['location'] <= range['max'] 
                and (x['range_percent'] >= MINIMUM_RANGE_EXPLORATION 
                     or phase_min != Decimal('0') or phase_max  != Decimal('1')),
                assignment_locations)
            
            # if they never left and they've been in the phase long enough
            if len(only_in_range) == len(assignment_locations):
                range['agreement'] +=1
                farthest_right = max(farthest_right, max(only_in_range, key = lambda x: x['location'])['location'])
        
        # Now snip the max to be just as large as the rightmost
        # most recent ping
        range['max'] = farthest_right
        
        ranges.append(range)
    logging.debug("Agreements: %s", (range,) )                
        
    return ranges

def groupByKey(iterable, key):
    """Splits all items into groups based on their value due to the key function"""
    group_iterable = dict()

    all_groups = set([key(i) for i in iterable])
    for group in all_groups:
        filtered_items = filter(lambda i: key(i) == group, iterable)
        group_iterable[group] = filtered_items
    
    return group_iterable

        
def phaseIsDivisible(phase):
    """ Returns True if the phase is large enough that 
    it can still be subdivided. """
    return (phase['max'] - phase['min'] > 0)
    

def takePicture(phase, video_id, db):
    """ Records a picture in the pictures table, given a converged
    phase """
    if phaseIsDivisible(phase):    
        raise Exception("Divisible phrase sent to takePicture")
    
    logging.debug("taking picture of phase %s" % phase['phase'])
    this_phase = phase['phase']
    
    sql = """INSERT INTO pictures (videoid, location, phase_list) VALUES (%s, %s, %s)"""
    db.query_and_return_array(sql, (video_id, phase['min'], phase['phase_list']))
    

def compareToHistoricalPhase(phase, servertime, db):
    """ Uses an older phase to mimic other people when there
    is nobody else around for this user to play with """
    
    older_phase = getNextHistoricalPhase(phase, db)
    
    if older_phase is None:
        logging.info("Keep waiting; no historical phases to refer to.") 
        return (False, None, None)
    else:
        # note that this phase list is using historical data
        sql = """UPDATE phase_lists, phases SET is_historical = TRUE
                WHERE phases.phase = %s 
                AND phases.phase_list = phase_lists.pk
        """
        db.query_and_return_array(sql, (phase['phase'], ))    
    
        # we should be able to call compareLocations on the older
        # phase and get the older result back, which we can use
        # to simulate what happened in the past
        return compareLocations(older_phase, older_phase['end'], db)    


def getNextHistoricalPhase(phase, db):
    """ Finds a previously identical phase to this one """
    
    # graph phases that were identical and eventually
    # led to a picture
    sql = """SELECT * FROM phases
             WHERE phase_list IN 
                (SELECT phase_lists.pk FROM phase_lists, pictures
                WHERE phase_lists.videoid = 
                    (SELECT videoid FROM phase_lists
                     WHERE phase_lists.pk = %s)
                AND phase_lists.pk = pictures.phase_list)
             AND min = %s AND max = %s
             LIMIT 1"""
    
    # Unexplained behavior of MySQLdb:
    # when I use the recommended query(sql, args), the Decimals
    # get converted in such a way that the two are not considered equal
    # but if I just % the string directly, it works. Go fig yur.
    result = db.query_and_return_array(sql % (phase['phase_list'], phase['min'], phase['max']))
    
    if len(result) == 0:
        return None
    else:
        return result[0]

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)
    
