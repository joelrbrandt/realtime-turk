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