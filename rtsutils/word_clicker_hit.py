import settings

from external_hit import *

from timeutils import unixtime
from datetime import datetime


DEFAULT_ASSIGNMENT_DURATION = 60*10
DEFAULT_LIFETIME = 60*10
DEFAULT_AUTO_APPROVAL_DELAY = 60*60*24*7

class WordClickerHit(ExternalHit):
    def __init__(self,
                 experiment_number,
                 waitbucket=120,
                 title = "Find verbs in a paragraph",
                 description = "Click to highlight all the verbs in a paragraph",
                 keywords = "text verbs reading quick",
                 frame_height = 1200,
                 reward_as_usd_float = 0.02,
                 assignment_duration = DEFAULT_ASSIGNMENT_DURATION,
                 lifetime = DEFAULT_LIFETIME,
                 max_assignments = 1,
                 auto_approval_delay = DEFAULT_AUTO_APPROVAL_DELAY,
                 use_conditions = True):
        
        url = "http://" + str(settings.HIT_SERVER) + "/" + str(settings.HIT_SERVER_USER_DIR) + "/word_clicker.mpy?experiment=" + str(experiment_number) + "&retainer=1&waittime=" + str(waitbucket)
        
        # default to just alert if we're not assigning to conditions
        if not use_conditions:
            url += "&alert=1&tetris=0&reward=0"
        
        ExternalHit.__init__(self, 
                             title=title, 
                             description=description,
                             keywords=keywords,
                             url=url,
                             frame_height=frame_height,
                             reward_as_usd_float=reward_as_usd_float,
                             assignment_duration=assignment_duration,
                             lifetime=lifetime,
                             max_assignments=max_assignments,
                             auto_approval_delay=auto_approval_delay)
        self.experiment_number = experiment_number
        self.waitbucket = waitbucket
        self.use_conditions = use_conditions

    def post(self, mt_conn, db_conn):
        hit = ExternalHit.post(self, mt_conn)
        sql = """INSERT INTO hits 
                    (hitid, hittypeid, experiment, creation_time, title, description, keywords, 
                     reward, assignment_duration, lifetime, max_assignments, auto_approval_delay, waitbucket)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        db_conn.query_and_return_array(sql, (hit.HITId, hit.HITTypeId, self.experiment_number, unixtime(datetime.now()), self.title, self.description, self.keywords,
                                             self.reward_as_usd_float, self.assignment_duration, self.lifetime, self.max_assignments, self.auto_approval_delay, self.waitbucket))
        return hit
