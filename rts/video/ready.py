from mod_python import apache, util

import json
from datetime import datetime
from itertools import groupby

from rtsutils.db_connection import DBConnection
from rtsutils.timeutils import *

import logging

VIDEO_SOURCE_DIR = 'media/videos/'

# source types
WEB_M = "webm"
OGG = "ogg"
MP4 = "mp4"

""" Writes to the request whether we need this particular worker to attack a video right now"""
def is_ready(request):
    request.content_type = "application/json"
    db = DBConnection()
    
    form = util.FieldStorage(request)
    workerid = unicode(form['workerid'].value)
    
    # we need distinct workers who have done an assignment on a video with fewer than "3" assignments
    now = unixtime(datetime.now())

    result = db.query_and_return_array("""SELECT videos.pk, workerid FROM videos LEFT JOIN assignments ON videos.pk = assignments.videoid GROUP BY videos.pk HAVING COUNT(DISTINCT workerid) <= 3 ORDER BY creationtime DESC""" )

    video_needed = False
    # relying on python groupby maintaining the order of the videos
    for videoid, rows in groupby(result, key=lambda row: row['pk']):
        workers = [row['workerid'] for row in rows]
        if workerid not in workers:
            # there's someone who needs our help!
            video_needed = True
            video = getVideo(videoid, request)
            request.write(json.dumps( video ) )
            break

    if not video_needed:
        # if we got here, there's nothing to do yet
        request.write(json.dumps( { 'is_ready' : False } ))


""" Writes the JSON for the video information to the request object"""
def getVideo(videoid, request):
    db = DBConnection()
    result = db.query_and_return_array("""SELECT width, height, has_mp4, has_webm, has_ogg, filename FROM videos WHERE pk = %s""", (videoid, ) )[0]

    json_out = dict()
    json_out['is_ready'] = True
    json_out['width'] = result['width']
    json_out['height'] = result['height']
    
    json_out['sources'] = []

    # this order matters! it affects the order the browsers look for the source files in. 
    # Go for the better encodings first.
    if result['has_webm']:
        json_out['sources'].append(createSource(result['filename'], WEB_M))
    if result['has_ogg']:
        json_out['sources'].append(createSource(result['filename'], OGG))
    if result['has_mp4']:
        json_out['sources'].append(createSource(result['filename'], MP4))

    return json_out

def createSource(filename, type):
    source = dict()

    if type == WEB_M:
        filetype = ".webm"
        videotype = 'video/webm; codecs="vp8, vorbis"';
    elif type == OGG:
        filetype = ".theora.ogv"
        videotype = 'video/ogg; codecs="theora, vorbis"'
    elif type == MP4:
        filetype = ".mp4"
        videotype = 'video/mp4; codecs="avc1.42E01E, mp4a.40.2"'
    source['src'] = VIDEO_SOURCE_DIR + filename + filetype
    source['type'] = videotype

    return source