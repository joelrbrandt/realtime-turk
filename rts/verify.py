from mod_python import apache, util
import MySQLdb
import simplejson as json
import settings

from rtsutils import word_clicker_approver

def verify(request):
    request.content_type = "application/json"

    form = util.FieldStorage(request)
    text_id = int(form['textid'].value)
    verbs = [int(field.value) for field in form.getlist('verbs[]')]
    
    result = word_clicker_approver.calculateAccuracy(text_id, verbs)
    request.write(json.dumps(result))
    
