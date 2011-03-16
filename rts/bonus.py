from mod_python import apache, util
import MySQLdb
import settings

def grantBonus(request):        
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    form = util.FieldStorage(request)
    worker_id = form['workerId'].value
    assignment_id = form['assignmentId'].value
    hit_id = form['hitId'].value
    
    cur.execute("""INSERT INTO bonuses (hit_id, worker_id, assignment_id, give_bonus, bonus_paid) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE give_bonus = %s""", (hit_id, worker_id, assignment_id, True, False, True))
        
    cur.close()
    db.close()
