from django.http import HttpResponse
from retainer.models import *

from datetime import datetime, timedelta
from retainer.utils.timeutils import unixtime

MIN_WAITING_WORKERS = 1

PING_TIMEOUT_SECONDS = 4  # how long ago we treat a ping as being current
PING_TYPES = {
    'waiting': 'ping-waiting',
    'working': 'ping-working',
    'showing': 'ping-showing',
}

# Get a task for the worker, or assign one if we can
def get_task(request, worker_id, assignment_id):
    # find out whether the worker has already been assigned a task. if so, just return that task.
    current_assignments = Assignments.objects.filter(assignment_id = assignment_id)
    if len(current_assignments) == 1:
        return get_task_info(current_assignments[0].task_id)

    # are there enough workers waiting?
    # if so, ask the application server to give us a task to do, or to decline giving a task
    num_waiting = num_waiting_workers()

    return HttpResponse(u'HI ' + worker_id)


# Given a task id, return a json object that describes that task
def get_task_info(task_id):
    return HttpResponse(u'There is a task and it is awesome: ' + task_id)


# Return the number of workers who are waiting on retainer right now
def num_waiting_workers():
    time_now = unixtime(datetime.now())
    time_ping_floor = unixtime(datetime.now() - timedelta(seconds = PING_TIMEOUT_SECONDS))
    print(time_now)
    print(time_ping_floor)

    #recent_pings = Events.objects.filter(event_type = PING_TYPES['waiting'])
