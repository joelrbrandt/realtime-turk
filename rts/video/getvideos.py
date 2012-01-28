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

    # get all videos and whether they are currently enabled and have no previous photos
    videos_in_db = db.query_and_return_array("""SELECT videos.pk, (location IS NOT NULL) AS hasphotos FROM videos 
       LEFT JOIN pictures ON pictures.videoid = videos.pk""")

    videos = []
    for video in videos_in_db:
        has_photos = bool(video['hasphotos'])
        curVideo = getVideo(video['pk'], create_phase=(not has_photos), restart_if_converged=True)
        curVideo['hasphotos'] = has_photos
        videos.append(curVideo)

    request.write(json.dumps(videos, cls = DecimalEncoder))


def indexNewVideos(db):
    to_post = getPostableVideos(db, directory=VIDEO_DIRECTORY)
    for video_to_post in to_post:
        video_path = os.path.abspath(VIDEO_DIRECTORY + video_to_post)
        logging.debug(video_path)
        encodeAndUpload(video_path)

