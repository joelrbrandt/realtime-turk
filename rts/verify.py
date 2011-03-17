from mod_python import apache, util
import MySQLdb
import simplejson as json
import settings

def verify(request):
    #request.content_type = "application/json"

    form = util.FieldStorage(request)
    text_id = int(form['textid'].value)
    verbs = [int(field.value) for field in form.getlist('verbs[]')]
    
    result = { 'precision': 0.70, 'recall': 0.70 }
    request.write(json.dumps(result))