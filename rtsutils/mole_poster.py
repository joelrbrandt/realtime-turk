from optparse import OptionParser
from datetime import datetime, timedelta
import time
import random
import os

import mole_hit
from mole_hit import *
from db_connection import *
from mt_connection import *
from timeutils import total_seconds, unixtime
from mole_approver import approve_mole_hits_and_clean_up
from work_approver import expire_all_hits

import settings

TIME_BETWEEN_RUNS = 5 # seconds
TIME_BETWEEN_HIT_POSTINGS = 30 # seconds

MIN_ON_RETAINER = 1
MIN_WHACKS_TO_DECIDE = 0

def postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db):
    """ Posts HITs of several possible varieties (creating multiple HIT groups) based on a random selection: will vary price and description """
    
    if random.random() > .5:
        price += 0.01
    
    if random.random() < .5:
        # defaults
        postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db)
    else:
        title = "Quick reaction: click on the photo"
        description = "We show an array of photos, you click on the one that is of the furry animal as soon as it appears."
        postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, title, description)

def postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, title = mole_hit.TITLE, description = mole_hit.DESCRIPTION):
    """ Posts HITs to MTurk with the given parameters"""

    h = MoleHit(waitbucket=max_wait_time,
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

            approve_mole_hits_and_clean_up(verbose=False, dry_run=False)
            #keep_going = postNewMoles(db)
            
            sleep(start_run)
    except KeyboardInterrupt:
        print("Caught Ctrl-C. Exiting...")
    finally:
        expire_all_hits(mt_conn)
        approve_mole_hits_and_clean_up(verbose=False, dry_run=False)


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
    need_votes = getMolesNeedingWhacks(db)
    print(need_votes)
    
    if num_waiting >= MIN_ON_RETAINER and len(need_votes) == 0:
        return postVotes(db)
    else:
        return True

def getMolesNeedingWhacks(db, workerid = None):
    return []

    #sql = """SELECT * FROM moles"""
    #need_whacks = db.query_and_return_array(sql)
    
    #completed = [row['moleid'] for row in db.query_and_return_array("""SELECT * FROM responses, assignments WHERE responses.assignmentid = assignments.assignmentid AND assignments.workerid = %s""", (workerid, ))]
    #logging.debug(need_whacks)
    #logging.debug(completed)
    
    #return [row for row in need_whacks if row['pk'] not in completed]


if __name__ == "__main__":
    if settings.SANDBOX:
        wait_bucket = 5
    else:
        wait_bucket = 60
    
#    if MIN_ON_RETAINER < 7 and not settings.SANDBOX:
#        raise Exception("Not enough people on retainer for non-sandbox tasks! Are you sure?")
#    if MIN_WHACKS_TO_DECIDE < 5 and not settings.SANDBOX:
#        raise Exception("Not enough votes needed for non-sandbox tasks! Are you sure?")

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
