from optparse import OptionParser
from datetime import datetime, timedelta
import time
import random
import os

import ab_hit
from ab_hit import *
from db_connection import *
from mt_connection import *
from timeutils import total_seconds, unixtime
from ab_approver import approve_ab_hits_and_clean_up
from work_approver import expire_all_hits

import settings

TIME_BETWEEN_RUNS = 5 # seconds
TIME_BETWEEN_HIT_POSTINGS = 30 # seconds

MIN_ON_RETAINER = 8
MIN_VOTES_TO_DECIDE = 5

def postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db):
    """ Posts HITs of several possible varieties (creating multiple HIT groups) based on a random selection: will vary price and description """
    
    if random.random() > .5:
        price += 0.01
    
    if random.random() < .5:
        # defaults
        postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db)
    else:
        title = "Snap judgment: Which is better?"
        description = "I have to make a choice. Which one is better?"
        postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, title, description)

def postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, title = ab_hit.TITLE, description = ab_hit.DESCRIPTION):
    """ Posts HITs to MTurk with the given parameters"""

    h = ABHit(waitbucket=max_wait_time,
                reward_as_usd_float=price,
                assignment_duration=max_wait_time+120,
                lifetime=expiration, title=title, description=description)

    for i in range(num_hits):
        try:
            hit = h.post(mt_conn, db)
            print "Posted HIT ID " + hit.HITId
        except Exception, e:
            print "Got exception posting HIT:\n" + str(e)

def quikTurKit(num_hits, max_wait_time, price, expiration):
    """ Keeps posting HITs """
    mt_conn = get_mt_conn()
    db = DBConnection()
    
    try:
        last_hit_post = datetime.now()
        postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db)

        keep_going = True
        while keep_going:
            start_run = datetime.now()
            printCurrentlyWaiting(db)
            
            if start_run - last_hit_post >= timedelta(seconds = TIME_BETWEEN_HIT_POSTINGS):
                postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db,)
                last_hit_post = start_run
                print("Warning: not approving HITs. Do in another script.")            

            # approve_video_hits_and_clean_up(verbose=False, dry_run=False)
            keep_going = postNewVotes(db)
            
            sleep(start_run)
    except KeyboardInterrupt:
        print("Caught Ctrl-C. Exiting...")
    finally:
        expire_all_hits(mt_conn)
        approve_ab_hits_and_clean_up(verbose=False, dry_run=False)


def printCurrentlyWaiting(db):
    ping_floor = datetime.now() - timedelta(seconds = 10)
    ping_types = ["ping-waiting", "ping-showing", "ping-working"]

    results = dict()
    for ping_type in ping_types:
        results[ping_type] = len(getPingStatus(db, ping_type))
        print(ping_type + ": unique assignmentIds pings in last 10 seconds: " + str(results[ping_type]))
    return results


def sleep(start_run):
    sleep_time = max(0, TIME_BETWEEN_RUNS - total_seconds(datetime.now() - start_run))
    print("Sleeping for %s seconds" % sleep_time)
    time.sleep(sleep_time)
    
def getPingStatus(db, event_type):
    ping_floor = unixtime(datetime.now() - timedelta(seconds = 4))
    sql = """SELECT logging.assignmentid, logging.servertime
        FROM logging, 
        (SELECT MAX(servertime) AS pingtime, assignmentid FROM logging WHERE servertime > %s AND event LIKE 'ping%%' GROUP BY assignmentid) AS mostRecent 
    WHERE logging.servertime = mostRecent.pingTime AND logging.assignmentid=mostRecent.assignmentid AND event = %s GROUP BY assignmentid"""
    result = db.query_and_return_array(sql, (ping_floor, event_type))
    return result


def postNewVotes(db):
    """ Will post a new vote session if there are enough people on retainer"""
    num_waiting = len(getPingStatus(db, 'ping-waiting'))
    
    # Are there unlabeled videos? If so, we shouldn't be adding new ones
    need_votes = getVotesNeedingOpinions(db)
    print(need_votes)
    
    if num_waiting >= MIN_ON_RETAINER and len(need_votes) == 0:
        return postVotes(db)
    else:
        return True

def haveCompleted(videoid, workerid, db):
    count = db.query_and_return_array("""SELECT COUNT(*) FROM slow_votes, assignments WHERE slow_votes.assignmentid = assignments.assignmentid AND videoid = %s AND workerid = %s""", (videoid, workerid))
    return count[0]['COUNT(*)']


def getVotesNeedingOpinions(db, workerid = None):
    sql = """SELECT * FROM votes LEFT JOIN responses ON (votes.pk = responses.voteid) GROUP BY votes.pk HAVING COUNT(*)<%s"""
    need_votes = db.query_and_return_array(sql, (MIN_VOTES_TO_DECIDE, ))
    
    completed = [row['voteid'] for row in db.query_and_return_array("""SELECT * FROM responses, assignments WHERE responses.assignmentid = assignments.assignmentid AND assignments.workerid = %s""", (workerid, ))]
    logging.debug(need_votes)
    logging.debug(completed)
    
    return [row for row in need_votes if row['pk'] not in completed]

new_votes = [
    dict({
        'question': "Which is scarier?",
        'images': [ "http://images2.layoutsparks.com/1/242580/Zombie-prisoner-frightening-eyes.jpg", "http://www.fearishere.com/screensavers/preview/halloween77_58.jpg"
        ]
    }),
    dict({
        'question': "Which person looks more heroic?",
        'images': [ "http://image.toutlecine.com/photos/h/e/r/heroic-trio-1993-01-g.jpg", "http://fineartamerica.com/images-medium/a-heroic-resistance-walter-girotto.jpg"]
    }),
    dict({
        'question': "Which logo looks better?",
        'images': [ "http://flock.csail.mit.edu/msbernst/media/color-1-01.png", "http://flock.csail.mit.edu/msbernst/media/color-2-01.png"]
    }),    
    dict({
        'question': "Which font looks better?",
        'images': [ "http://flock.csail.mit.edu/msbernst/media/font-1-01.png", "http://flock.csail.mit.edu/msbernst/media/font-2-01.png"]
    })
]
new_votes.reverse()

def postVotes(db):            
    if len(new_votes) > 0:
        
        to_post = new_votes.pop()
        print("Vote being posted: %s" % to_post)
        theTime = unixtime(datetime.now())
        vote_id = db.query_and_return_insert_id("""INSERT INTO votes (question, creation_time) VALUES (%s, %s)""", (to_post['question'], theTime,) )
        
        for option in to_post['images']:
            db.query_and_return_array("""INSERT INTO vote_options (voteid, `option`) VALUES (%s, %s)""", (vote_id, option))        
        return True
    else:
        print("Nothing to post")
        return False

if __name__ == "__main__":
    if settings.SANDBOX:
        wait_bucket = 5 * 60
    else:
        wait_bucket = 5 * 60
    
    if MIN_ON_RETAINER < 7 and not settings.SANDBOX:
        raise Exception("Not enough people on retainer for non-sandbox tasks! Are you sure?")
    if MIN_VOTES_TO_DECIDE < 5 and not settings.SANDBOX:
        raise Exception("Not enough votes needed for non-sandbox tasks! Are you sure?")

    # Parse the options
    parser = OptionParser()
    parser.add_option("-n", "--number-of-hits", dest="number_of_hits", help="NUMBER of hits", metavar="NUMBER", default = 5)
    parser.add_option("-b", "--wait-bucket", dest="waitbucket", help="number of SECONDS to wait on retainer", metavar="SECONDS", default = wait_bucket)
    parser.add_option("-p", "--price", dest="price", help="number of CENTS to pay", metavar="CENTS", default = 3)
    parser.add_option("-x", "--expiration-time", dest="expiration", help="number of seconds before hit EXPIRES", metavar="EXPIRES", default = 10 * 60)

    (options, args) = parser.parse_args()

    n = int(options.number_of_hits)
    b = int(options.waitbucket)
    p = int(options.price)/100.0
    x = int(options.expiration)

    quikTurKit(n, b, p, x)