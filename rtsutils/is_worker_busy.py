import settings
import MySQLdb

def isWorkerBusy(worker_id):
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    open_hits = getAcceptedHITs(worker_id, cur)
    open_and_alive_hits = filter(lambda x: isExpired(x, cur), open_hits)
    
    cur.close()
    db.close()
    
    return len(open_and_alive_hits) > 0
    
def getAcceptedHITs(worker_id, cur):
    """Returns a list of all HITs where the last word was that the worker had accepted it"""
    open_hits = []

    # this gives us the last notification we got for any HIT that this worker touched
    cur.execute("""SELECT eventtype, notifications.assignmentid, hitid
    FROM notifications
    RIGHT JOIN logging ON notifications.assignmentid = logging.assignmentid
    WHERE logging.workerid =  %s
    AND logging.event =  'accept'
    AND TIMESTAMP = ( 
    SELECT MAX( TIMESTAMP ) 
    FROM notifications n2
    WHERE n2.assignmentid = notifications.assignmentid ) 
    GROUP BY notifications.assignmentid""", (worker_id,) )    
    
    for row in cur.fetchall():
        # if they submitted or returned the HIT, it's not active any more
        if row['eventtype'] == 'AssignmentSubmitted' or row['eventtype'] == 'AssignmentReturned':
            continue
        
        if row['eventtype'] == 'AssignmentAccepted':
            # if the last message was an accept, we should be worried            
            open_hits.append(row)
    
    return open_hits
    
def isExpired(hit, cur):
    """ Removes any HITs that have expired or become otherwise reviewable """
    cur.execute("""SELECT eventtype, max(timestamp), hitid FROM notifications WHERE hitid = %s""", (hit['hitid'], ))
    result = cur.fetchone()
    
    # filter it out if the HIT has expired
    return result['eventtype'] in ['HITExpired', 'HITReviewable']