import time
import threading

from datetime import datetime

class WorkQueue():
    def __init__(self):
        self._work_queue = []

        self._work_queue_cv = threading.Condition()


    def addWork(self, work_unit_array):
        with self._work_queue_cv:
            self._work_queue.extend(work_unit_array)

            # Why notify all (instead of notify)? Well, three reasons:
            #  1. the first notified worker may not be interested in the work
            #  2. may often add multiple work units in one call
            #  3. in future versions of python, "notify" is not guaranteed to notify exactly 1 waiting thread anyway
            self._work_queue_cv.notifyAll()
            return len(self._work_queue)

    # this method gets work if available, and otherwise returns immediately.
    # it does not block (except to acquire initial lock)
    #
    # can optionally provide an 'evaluator' function, which determines if the work
    # is to be accepted by this worker. The entire queue is looked through until
    # the evaluator returns True or the end is reached
    def getWork(self, evaluator=lambda w: True):
        with self._work_queue_cv:
            work = None
            for i in range(len(self._work_queue)):
                if evaluator(self._work_queue[i]):
                    work = self._work_queue.pop(i)
                    break
            return work


    def waitForWork(self, timeout=30, evaluator=lambda w: True):
        with self._work_queue_cv:
            start = datetime.now()
            timeout_remaining = timeout

            work = self.getWork(evaluator)
            while work == None and timeout_remaining > 0:
                self._work_queue_cv.wait(timeout_remaining)
                work = self.getWork(evaluator)
                timeout_remaining = getRemainingTimeout(start, timeout)
            
            return work


#
# Helper Functions
#

# given a start time (datetime) and a total timeout (in seconds), this function
# computes how long it has been since starttime, and subtracts that from
# the total timeout
# returns an int in the range [0,total_timeout]
def getRemainingTimeout(start, total_timeout):
    td = datetime.now() - start
    elapsed = td.days * 3600 * 24 + td.seconds + td.microseconds / 1000000
    remaining = total_timeout - elapsed
    return max(min(int(remaining), int(total_timeout)), 0)
    

#
# Testing components
#

class WorkAddTester(threading.Thread):
    def __init__(self, work_queue, delay=5):
        threading.Thread.__init__(self)
        self.daemon=True
        self._work_queue = work_queue
        self._delay = delay
        self._counter = 0
        self._stop = False


    def run(self):
        while not self._stop:
            self._work_queue.addWork([self._counter])
            self._counter += 1
            time.sleep(self._delay)

    def stop(self):
        self._stop = True


    
    
        
