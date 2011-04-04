from mod_python import apache, util
import simplejson as json

from rts import rts_logging
import logging

from rtsutils.db_connection import DBConnection
import ready

def getRandomVideo(request):
    request.content_type = "application/json"
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value
    
    db = DBConnection()    
    videoid = form['videoid'].value
    if videoid != None:
        videoid = int(videoid)
    else:    
        # TODO: this will not scale once we have over ~10,000 rows
        videoid = db.query_and_return_array("""SELECT pk FROM videos ORDER BY RAND() LIMIT 1""")[0]['pk']
        
    video_json = ready.getAndAssignVideo(assignmentid, videoid)
    request.write(json.dumps(video_json, use_decimal=True))
