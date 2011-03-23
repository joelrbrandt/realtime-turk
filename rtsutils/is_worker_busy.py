import settings
from rtsutils.db_connection import DBConnection
from datetime import datetime, timedelta

#TODO: time out open assignments after 60 minutes anyway, as a precaution

def isWorkerBusy(worker_id, ignore_assignments = []):    
    open_hits = getWorkerOpenHITs(worker_id)
    filtered = [x for x in open_hits if x not in ignore_assignments]
    return len(filtered) > 0
    
def getWorkerOpenHITs(worker_id):
    """Returns a list of all HITs where the last word was that the worker had accepted it"""
    open_hits = []

    # this gives us the last notification we got for any HIT that this worker touched
    db = DBConnection()
    results = db.query_and_return_array("""SELECT `assignment_duration`, `accept`, `return`, `submit`, `assignmentid` FROM hits, assignments WHERE assignments.hitid = hits.hitid AND assignments.workerid = %s """, (worker_id,) )
    
    for row in results:
        is_done = row['submit'] is not None
        is_returned = row['return'] is not None
        
        assignment_elapses = datetime.fromtimestamp(row['accept']) + timedelta(seconds = row['assignment_duration'])
        is_expired = (datetime.now() > assignment_elapses)
        
        if not is_done and not is_returned and not is_expired:
            open_hits.append(row['assignmentid'])
    
    return open_hits