from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection

import os

from rts import rts_logging
import logging

from rtsutils.video_poster import encodeAndUpload, getPostableVideos
from ready import getVideo
from location_ping import DecimalEncoder

VIDEO_DIRECTORY = os.path.dirname(__file__) + '/../../web/media/videos/'

def getVideos(request):
    request.content_type = "application/json"
    db = DBConnection()

    indexNewVideos(db)

    # get all videos that are not currently enabled and have no previous photos
    disabled = [ row['pk'] for row in db.query_and_return_array("""SELECT videos.pk FROM videos LEFT JOIN pictures ON pictures.videoid = videos.pk WHERE enabled = FALSE AND location IS NULL""")]

    videos = []
    for video in disabled:
        videos.append(getVideo(video))

    request.write(json.dumps(videos, cls = DecimalEncoder))

def indexNewVideos(db):
    to_post = getPostableVideos(db, directory=VIDEO_DIRECTORY)
    for video_to_post in to_post:
        encodeAndUpload(VIDEO_DIRECTORY + to_post)
