import os, math

from db_connection import DBConnection
from video_poster import VIDEO_DIRECTORY
from video_encoder import JPG_DIRECTORY

VIDEO_HOST_DIRECTORY = 'media/videos/' + JPG_DIRECTORY + os.sep

def getPhotos(filename):
    db = DBConnection()
    locations = db.query_and_return_array("""SELECT DISTINCT location FROM pictures, videos WHERE pictures.videoid = videos.pk AND videos.filename = %s""", (filename, ))
    
    # don't forget off-by-one: slider starts at 0, but first photo is photo1.jpg
    filenumbers = ['%03d' % min(int(row['location'] * 100 + 1), 100) for row in locations]
    
    return [VIDEO_HOST_DIRECTORY + filename + filenumber + '.jpg' for filenumber in filenumbers]
    
def getSlowPhotos(videoid, limit):
    db = DBConnection()
    locations = db.query_and_return_array("""SELECT filename, location FROM slow_snapshots, assignments, videos WHERE slow_snapshots.assignmentid = assignments.assignmentid AND videos.pk = assignments.videoid AND assignments.videoid = %s ORDER BY slow_snapshots.pk ASC LIMIT %s""", (videoid, limit))
    
    filename = locations[0]['filename']
    
    # don't forget off-by-one: slider starts at 0, but first photo is photo1.jpg
    filenumbers = set(['%03d' % min(int(row['location'] * 100 + 1), 100) for row in locations]) # use set() so we don't get copies
    
    return [VIDEO_HOST_DIRECTORY + filename + filenumber + '.jpg' for filenumber in filenumbers]
    