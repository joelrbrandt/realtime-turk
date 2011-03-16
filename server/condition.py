from mako.template import Template
import MySQLdb
import settings

CONDITIONS = [
    {
        name: 'baseline',
        is_alert: False,
        is_reward: False
    },
    {
        name: 'alert',
        is_alert: True,
        is_reward: False
    },
    {
        name: 'reward',
        is_alert: False,
        is_reward: True
    }
]

def loadCondition(request):
    """ Sees if the worker has already been assigned a condition, and if not, assigns them """
    
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    form = util.FieldStorage(request)
    workerid = form['workerid'].value
    
    num_rows = cur.execute("""SELECT is_alert, is_reward FROM workers WHERE workerid = %s """, (workerid, ) )
    if (num_rows == 0): # not in database yet
        setRandomCondition(worker_id, cur)
    else:
        
    

    
    renderTemplate(request, is_alert, is_reward)
    
def setRandomCondition(worker_id, cursor):
    """ Chooses a random group to assign the worker to, and sets it in the database """
    
    
def renderTemplate(request, is_alert, is_reward):
    """ Renders the worker's settings into the javascript """
    template = Template(filename='/var/www/realtime/msbernst/server/condition.js')

    request.write(template.render(workerid_is_alert = is_alert, workerid_is_reward = is_reward))