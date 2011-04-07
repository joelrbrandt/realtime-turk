import settings
import random
import simplejson as json

from rtsutils.db_connection import DBConnection

CONDITIONS = [
    {
        'name': 'baseline',
        'is_alert': False,
        'is_reward': False,
        'is_tetris': False
    },
    {
        'name': 'alert',
        'is_alert': True,
        'is_reward': False,
        'is_tetris': False
    },
    {
        'name': 'reward',
        'is_alert': True,
        'is_reward': True,
        'is_tetris': False
    },
    {
        'name': 'tetris',
        'is_alert': True,
        'is_reward': False,
        'is_tetris': True
    }    
]

def getConditionName(is_alert, is_reward, is_tetris):
    for condition in CONDITIONS:
        if condition['is_alert'] == is_alert and condition['is_reward'] == is_reward and condition['is_tetris'] == is_tetris:
            return condition['name']
    
    # we don't know it
    return 'unknown'

def isAlert(worker_id):
    """ Returns true if the worker should have an alert """
    return getCondition(worker_id)['isAlert']

def isReward(worker_id):
    """ Returns true if the worker should get a bonus """
    return getCondition(worker_id)['isReward']
    
def isTetris(worker_id):
    """ Returns true if the worker should play Tetris """
    return getCondition(worker_id)['isTetris']

def getCondition(worker_id):
    """ Sees if the worker has already been assigned a condition, and if not, assigns them """
    
    db=DBConnection()
    
    rows = db.query_and_return_array("""SELECT is_alert, is_reward, is_tetris FROM workers WHERE workerid = %s """, (worker_id, ) )
    if len(rows) == 0: # not in database yet
        result = setRandomCondition(worker_id)
    else:
        result = rows[0]
    is_alert = bool(result['is_alert'])
    is_reward = bool(result['is_reward'])
    is_tetris = bool(result['is_tetris'])
    
    return { 'isAlert': is_alert,
             'isReward': is_reward,
             'isTetris': is_tetris }
    
def setRandomCondition(worker_id):
    """ Chooses a random group to assign the worker to, and sets it in the database """
    random_condition = random.choice(CONDITIONS)
    
    db=DBConnection()    
    db.query_and_return_array("""INSERT INTO workers (workerid, is_alert, is_reward, is_tetris, read_instructions) VALUES (%s, %s, %s, %s, FALSE) ON DUPLICATE KEY UPDATE is_alert=%s, is_reward=%s, is_tetris=%s, read_instructions=FALSE""", (worker_id, random_condition['is_alert'], random_condition['is_reward'], random_condition['is_tetris'], random_condition['is_alert'], random_condition['is_reward'], random_condition['is_tetris']) )
    
    return random_condition

def renderResponse(request, is_alert, is_reward, is_tetris):
    from mod_python import apache, util # we don't want this available for all code, just this
    
    response = {
                    'is_alert': is_alert,
                    'is_reward': is_reward,
                    'is_tetris': is_tetris
                }
    request.write(json.dumps(response))
    
def randomizeConditions(do_you_mean_it="NO"):
    if do_you_mean_it != "YES_I_MEAN_IT":
        print """
This will assign all workerids to a new random condition. Do not do this lightly!\n
Call with randomizeConditions('YES_I_MEAN_IT')
"""
        return 0

    else:
        print("Assigning all workers to a new random condition")
        db=DBConnection()
        
        # get all workers, randomize them one by one
        result = db.query_and_return_array("""SELECT workerid FROM workers""")
        workers = [row['workerid'] for row in result]
        for worker in workers:
            setRandomCondition(worker)