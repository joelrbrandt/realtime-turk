from optparse import OptionParser
from datetime import datetime, timedelta
import time
import random
import os


from video_hit import *
from db_connection import *
from mt_connection import *
from timeutils import total_seconds, unixtime
from video_approver import approve_video_hits_and_clean_up
from work_approver import expire_all_hits
#from break_handler import BreakHandler
import video_hit
import video_encoder
import settings

TIME_BETWEEN_RUNS = 5 # seconds
TIME_BETWEEN_HIT_POSTINGS = 30 # seconds
VIDEO_DIRECTORY = '../web/media/videos/'

MIN_ON_RETAINER = 4
PHOTOGRAPHER_ID = "photographer"
MAX_WORKERS_PER_VIDEO = 10

def postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, version):
    """ Posts HITs of several possible varieties (creating multiple HIT groups) based on a random selection: will vary price and description """
    
    if random.random() > .5:
        price += 0.01
    
    if random.random() < .5:
        # defaults
        postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, version = version)
    else:
        title = "TurkCamera: help take a good picture"
        description = "I took a short movie rather than a picture. Help find the best photographic moments in it."        
        postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, title, description, version)

def postHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, title = video_hit.TITLE, description = video_hit.DESCRIPTION, version='fast'):
    """ Posts HITs to MTurk with the given parameters"""

    h = VideoHit(waitbucket=max_wait_time,
                reward_as_usd_float=price,
                assignment_duration=max_wait_time+120,
                lifetime=expiration, title=title, description=description,
                version=version)

    for i in range(num_hits):
        try:
            hit = h.post(mt_conn, db)
            print "Posted HIT ID " + hit.HITId
        except Exception, e:
            print "Got exception posting HIT:\n" + str(e)

def quikTurKit(num_hits, max_wait_time, price, expiration, version):
    """ Keeps posting HITs """
    mt_conn = get_mt_conn()
    db = DBConnection()
    
    try:
        last_hit_post = datetime.now()
        postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, version)

        keep_going = True
        while keep_going:
            start_run = datetime.now()
            printCurrentlyWaiting(db)
            
            if start_run - last_hit_post >= timedelta(seconds = TIME_BETWEEN_HIT_POSTINGS):
                postRandomHITs(num_hits, max_wait_time, price, expiration, mt_conn, db, version)
                last_hit_post = start_run
                print("Warning: not approving HITs. Do in another script.")            

            # approve_video_hits_and_clean_up(verbose=False, dry_run=False)
            keep_going = postNewVideos(db, version)
            
            sleep(start_run)
    except KeyboardInterrupt:
        print("Caught Ctrl-C. Exiting...")
    finally:
        expire_all_hits(mt_conn)
        approve_video_hits_and_clean_up(verbose=False, dry_run=False)


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
    ping_floor = unixtime(datetime.now() - timedelta(seconds = 10))
    sql = """SELECT logging.assignmentid, logging.servertime
        FROM logging, 
        (SELECT MAX(servertime) AS pingtime, assignmentid FROM logging WHERE servertime > %s AND event LIKE 'ping%%' GROUP BY assignmentid) AS mostRecent 
    WHERE logging.servertime = mostRecent.pingTime AND logging.assignmentid=mostRecent.assignmentid AND event = %s GROUP BY assignmentid"""
    result = db.query_and_return_array(sql, (ping_floor, event_type))
    return result


def postNewVideos(db, version):
    """ Will post a new video if there are enough people on retainer"""
    num_waiting = len(getPingStatus(db, 'ping-waiting'))
    
    # Are there unlabeled videos? If so, we shouldn't be adding new ones
    unlabeled = unlabeledVideos(db, version == "slow")
    print(unlabeled)
    
    if num_waiting >= MIN_ON_RETAINER and len(unlabeled) == 0:
        return postVideo(db, version)
    else:
        return True

def unlabeledVideos(db, is_slow):
    """ Returns videos that need to be Turked """
    
    # we need videos that have no pictures yet
    if is_slow:        
        inner_query = "SELECT COUNT(*) AS numPictures, videoid FROM slow_snapshots, assignments WHERE slow_snapshots.assignmentid = assignments.assignmentid AND workerid <> '" + PHOTOGRAPHER_ID + "' GROUP BY videoid"
        num_pics_condition = 'OR pictureCount.numPictures < 3'
    else:
        inner_query = "SELECT COUNT(*) AS numPictures, videoid FROM pictures GROUP BY videoid"
        num_pics_condition = ''

    ping_floor = unixtime(datetime.now() - timedelta(seconds = 10))
    
    result = db.query_and_return_array("""
        SELECT pk FROM videos
        
        LEFT JOIN (""" + inner_query + """)
        AS pictureCount
        ON pictureCount.videoid = videos.pk

        LEFT JOIN (SELECT COUNT(DISTINCT assignments.assignmentid) AS numWorkers, videoid
                   FROM assignments, (SELECT MAX(servertime) AS pingtime, assignmentid FROM logging WHERE 
                   servertime > %s AND event LIKE 'ping%%' GROUP BY assignmentid) AS recentPing 
                   WHERE recentPing.assignmentid = assignments.assignmentid GROUP BY videoid)
        AS workerCount
        ON workerCount.videoid = videos.pk
        
        WHERE (pictureCount.numPictures IS NULL """ + num_pics_condition + """) 
        AND videos.enabled = TRUE
        AND (workerCount.numWorkers <= """ + str(MAX_WORKERS_PER_VIDEO) + """ OR workerCount.numWorkers IS NULL) 
        
        ORDER BY videos.pk DESC """, (ping_floor, ))
    return result


def postVideo(db, version):
    if version == "slow":
        column = "slow_available"
        date_column = "slow_available_time"
    else:
        column = "fast_available"
        date_column = "fast_available_time"        
        
    to_post = db.query_and_return_array("""SELECT videos.pk, videos.filename FROM videos, study_videos WHERE videos.pk = study_videos.videoid AND study_videos.""" + column + """ = FALSE ORDER BY RAND() LIMIT 1""")
    
    if len(to_post) > 0:
        
        print("Video being posted: %s" % to_post)
        
        db.query_and_return_array("""UPDATE study_videos SET """ + column + """ = TRUE, """ + date_column + """ = %s WHERE videoid = %s""", (unixtime(datetime.now()), to_post[0]['pk'] ))
        return True
    else:
        print("Nothing to post")
        return False
    
    """
    # get posted videos
    dirList = os.listdir(VIDEO_DIRECTORY)
    in_directory = filter(lambda x: x.endswith('.3gp'), dirList)
    
    available_to_post = [item for item in in_directory if item[:-4] not in in_db]
    if len(available_to_post) > 0:
        encodeAndUpload(VIDEO_DIRECTORY + random.choice(available_to_post))
    else:  
        print("Nothing to post")
    """

def encodeAndUpload(filename):
    (head, name, extension) = video_encoder.splitPath(filename)

    (width, height) = video_encoder.encodeVideo(head, name, extension)
    video_encoder.uploadVideo(name, width, height)


if __name__ == "__main__":
    if settings.SANDBOX:
        wait_bucket = 4 * 60
    else:
        wait_bucket = 4 * 60
    
    if MIN_ON_RETAINER < 4 and not settings.SANDBOX:
        raise Exception("Not enough people on retainer for non-sandbox tasks! Are you sure?")

    # Parse the options
    parser = OptionParser()
    parser.add_option("-n", "--number-of-hits", dest="number_of_hits", help="NUMBER of hits", metavar="NUMBER", default = 3)
    parser.add_option("-b", "--wait-bucket", dest="waitbucket", help="number of SECONDS to wait on retainer", metavar="SECONDS", default = wait_bucket)
    parser.add_option("-p", "--price", dest="price", help="number of CENTS to pay", metavar="CENTS", default = 4)
    parser.add_option("-x", "--expiration-time", dest="expiration", help="number of seconds before hit EXPIRES", metavar="EXPIRES", default = 10 * 60)
    parser.add_option("-v", "--version", dest="version", help="VERSION of study (slow, fast)", metavar="VERSION", default = "fast")    

    (options, args) = parser.parse_args()

    n = int(options.number_of_hits)
    b = int(options.waitbucket)
    p = int(options.price)/100.0
    x = int(options.expiration)
    v = options.version

    quikTurKit(n, b, p, x, v)
