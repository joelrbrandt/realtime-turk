from mod_python import apache, util
import MySQLdb
import settings
import simplejson as json

def getAgreement(request):
    request.content_type = "application/json"
    
    form = util.FieldStorage(request)
    worker_id = form['workerid'].value
    
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor()
    
    cur.execute("""SELECT read_instructions FROM workers WHERE workerid = %s""", (worker_id, ))
    
    result = { 'read_instructions': bool(cur.fetchone()[0]) }
    request.write(json.dumps(result))
    
def setAgreement(request):
    form = util.FieldStorage(request)
    worker_id = form['workerid'].value
    
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor()
    
    cur.execute("""UPDATE workers SET read_instructions = TRUE WHERE workerid = %s""", (worker_id, ))