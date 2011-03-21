from xml.sax.saxutils import escape

import logging
import settings

from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price

class ExternalHit():
    def __init__(self, title, description, keywords, url, frame_height, 
                 reward_as_usd_float, assignment_duration, lifetime, max_assignments, auto_approval_delay):
        self.title = title
        self.description = description
        self.keywords = keywords
        self.url = url
        self.frame_height = frame_height
        self.reward_as_usd_float = reward_as_usd_float
        self.assignment_duration = assignment_duration
        self.lifetime = lifetime
        self.max_assignments = max_assignments
        self.auto_approval_delay = auto_approval_delay
        self._question = ExternalQuestion(escape(self.url), self.frame_height)
        self._price = Price(self.reward_as_usd_float)


    def post(self, conn):
        return conn.create_hit(hit_type=None,
                               question=self._question,
                               lifetime=self.lifetime,
                               max_assignments=self.max_assignments,
                               title=self.title,
                               description=self.description,
                               keywords=self.keywords,
                               reward=self._price,
                               duration=self.assignment_duration,
                               approval_delay=self.auto_approval_delay,
                               annotation=None,
                               qual_req=None,
                               questions=None,
                               qualifications=None,
                               response_groups=None)

