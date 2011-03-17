from mod_python import apache, util
import MySQLdb
import simplejson as json
import settings

def verify(request):
    #request.content_type = "application/json"

    form = util.FieldStorage(request)
    text_id = int(form['textid'].value)
    verbs = [int(field.value) for field in form.getlist('verbs[]')]
    
    result = calculateAccuracy(text_id, verbs)
    request.write(json.dumps(result))
    
def calculateAccuracy(text_id, verbs):
    """ Looks up the ground truth in the database and calculates precision and recall. """
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor()
    
    cur.execute("""SELECT wordid FROM groundtruth WHERE textid = %s""", (text_id))
    ground_truth = [row[0] for row in cur.fetchall()]
    
    precision = float(len(set(verbs).intersection(ground_truth))) / len(verbs)
    recall = float(len(set(verbs).intersection(ground_truth))) / len(ground_truth)
    return { 'precision': precision, 'recall': recall }
    