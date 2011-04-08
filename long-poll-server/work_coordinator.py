import logging

import work_queue

class WorkCoordinator():
    def __init__(self):
        self._work_queue = work_queue.WorkQueue()

    def process(self, c):
        r = None

        logging.debug("processing command: " + str(c))
        if c['command'] == 'addwork':
            if c.has_key('data'):
                l = self._work_queue.addWork([c['data'],])
            r = {'response': 'success', 'pending_jobs':l}

        elif c['command'] == 'waitwork':
            w = self._work_queue.waitForWork()
            r = {'response': 'success', 'work':w}

        else:
            r = {'response': 'error', 'message': 'unknown command: ' + str(c['command'])}

        return r


