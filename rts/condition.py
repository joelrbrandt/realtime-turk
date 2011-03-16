from mod_python import apache, util
import MySQLdb
import settings
import random
import simplejson as json

CONDITIONS = [
    {
        'name': 'baseline',
        'is_alert': False,
        'is_reward': False
    },
    {
        'name': 'alert',
        'is_alert': True,
        'is_reward': False
    },
    {
        'name': 'reward',
        'is_alert': True,
        'is_reward': True
    }
]

def loadCondition(request):
    """ Sees if the worker has already been assigned a condition, and if not, assigns them """
    
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    form = util.FieldStorage(request)
    worker_id = form['workerid'].value
    
    num_rows = cur.execute("""SELECT is_alert, is_reward FROM workers WHERE workerid = %s """, (worker_id, ) )
    if (num_rows == 0): # not in database yet
        result = setRandomCondition(worker_id, cur)
    else:
        result = cur.fetchone()
    is_alert = bool(result['is_alert'])
    is_reward = bool(result['is_reward'])
    
    renderResponse(request, is_alert, is_reward)
    
def setRandomCondition(worker_id, cursor):
    """ Chooses a random group to assign the worker to, and sets it in the database """
    random_condition = random.choice(CONDITIONS)
    
    cursor.execute("""INSERT INTO workers (workerid, is_alert, is_reward) VALUES (%s, %s, %s)""", (worker_id, random_condition['is_alert'], random_condition['is_reward']) )
    
    return random_condition

def renderResponse(request, is_alert, is_reward):
    response = {
                    'is_alert': is_alert,
                    'is_reward': is_reward
                }
    request.write(json.dumps(response))
    
def renderTemplate(request, is_alert, is_reward):
    """ Renders the worker's settings into the javascript """
    from mako.template import Template
    template = Template(filename='/var/www/realtime/msbernst/server/condition.js')

    request.write(template.render(workerid_is_alert = is_alert, workerid_is_reward = is_reward))