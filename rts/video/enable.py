from mod_python import apache, util
import json

from rtsutils.db_connection import DBConnection

from rts import rts_logging
import logging

def enableVideo(request):
    # request.content_type = "application/json"
    db = DBConnection()

    form = util.FieldStorage(request)
    videoid = form['videoid'].value

    db.query_and_return_array("""UPDATE videos SET enabled = TRUE WHERE pk = %s""", (videoid, ))

def disableVideo(request):
    db = DBConnection()
    form = util.FieldStorage(request)
    videoid = form['videoid'].value

    db.query_and_return_array("""DELETE FROM pictures WHERE videoid = %s""", (videoid, ))
    db.query_and_return_array("""UPDATE videos SET enabled = FALSE WHERE pk = %s""", (videoid, ))
