from mod_python import apache, util
import MySQLdb
import simplejson as json
import settings

def getText(request):    
    request.content_type = "application/json"
    
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    form = util.FieldStorage(request)
    id = int(form['textid'].value)
        
    cur.execute("""SELECT html FROM texts WHERE pk = %s""", (id,))
    
    text = cur.fetchone()
    paragraph = text['html']
    
    result = dict()
    result['pk'] = id
    result['text'] = paragraph
    
    request.write(json.dumps(result))
        
    cur.close()
    db.close()
