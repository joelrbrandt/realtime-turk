from mod_python import apache, util
import MySQLdb
import simplejson as json
import settings
import parseresults

def status(request):    
    request.content_type = "application/json"
    
    form = util.FieldStorage(request)
    experiment = int(form['experiment'].value)    

    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor()    
    
    count = parseresults.printCurrentlyActiveCount(cur, experiment)
    result = { 'waiting': count }
    
    request.write(json.dumps(result))
        
    cur.close()
    db.close()
