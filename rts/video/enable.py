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

### TODO: write a parallel "disable and remove all pictures" to reset the demo more easily
