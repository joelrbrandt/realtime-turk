from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection
import ready

def getRandomVideo(request):
    request.content_type = "application/json"
    form = util.FieldStorage(request)
    assignmentid = form['assignmentid'].value

    db = DBConnection()
    # TODO: this will not scale once we have over ~10,000 rows
    random_id = db.query_and_return_array("""SELECT pk FROM videos ORDER BY RAND() LIMIT 1""")[0]['pk']
    video_json = ready.getAndAssignVideo(assignmentid, random_id)
    request.write(json.dumps(video_json))
