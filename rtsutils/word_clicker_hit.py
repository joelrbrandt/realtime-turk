import settings

from external_hit import *


DEFAULT_ASSIGNMENT_DURATION = 60*10
DEFAULT_LIFETIME = 60*10
DEFAULT_AUTO_APPROVAL_DELAY = 60*60*24*7

class WordClickerHit(ExternalHit):
    def __init__(self,
                 experiment_number,
                 title = "test",
                 description = "this is a test",
                 keywords = "test helloworld",
                 frame_height = 1200,
                 reward_as_usd_float = 0.02,
                 assignment_duration = DEFAULT_ASSIGNMENT_DURATION,
                 lifetime = DEFAULT_LIFETIME,
                 max_assignments = 1,
                 auto_approval_delay = DEFAULT_AUTO_APPROVAL_DELAY):
        ExternalHit.__init__(self, 
                             title=title, 
                             description=description,
                             keywords=keywords,
                             url="http://" + str(settings.HIT_SERVER) + "/" + str(settings.HIT_SERVER_USER_DIR) + "/word_clicker.mpy?experiment=" + str(experiment_number) + "&retainer=1",
                             frame_height=frame_height,
                             reward_as_usd_float=reward_as_usd_float,
                             assignment_duration=assignment_duration,
                             lifetime=lifetime,
                             max_assignments=max_assignments,
                             auto_approval_delay=auto_approval_delay)


