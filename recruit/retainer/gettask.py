from django.http import HttpResponse
import json
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
    if len(current_assignments) > 0 and current_assignments[0].task_id is not None:
        task_info = get_task_info(current_assignments[0].task_id)
    else:
        # are there enough workers waiting?
        # if so, ask the application server to give us a task to do, or to decline giving a task
        waiting_assignments = waiting_workers()
        if len(waiting_assignments) >= MIN_WAITING_WORKERS:
            worker_map = get_assignment_task_map(waiting_assignments)
            save_assignment_task_map(worker_map)
        
            # now we get the current worker's task out of that map and return it to the client
            current_worker_task = waiting_assignments[assignment_id]
            task_info = get_task_info(current_worker_task)
        else:
            # not enough workers, return no job
            task_info = { 'task_id': None }

    # now turn the task_info python into JSON to return to the client
    serialized = json.dumps(task_info)
    return HttpResponse(serialized, mimetype="application/json")


# Return the number of workers who are waiting on retainer right now
def waiting_workers():
    time_now = unixtime(datetime.now())
    time_ping_floor = unixtime(datetime.now() - timedelta(seconds = PING_TIMEOUT_SECONDS))
    print(time_now)
    print(time_ping_floor)

    recent_pings = Assignments.objects.filter(events__event_type = 'ping-waiting', events__server_time__gte = 0)
    #recent_workers = recent_pings.values('worker_id').distinct()
    #worker_ids = [worker['worker_id'] for worker in recent_

    return recent_pings


def save_assignment_task_map(assignment_map):
    for assignment_id in assignment_map.keys():
        task_id = assignment_map[assignment_id]
        assignment = Assignments.objects.get(assignment_id = assignment_id)
        assignment.task_id = task_id
        assignment.save()






# ~~~~~~~~~~~~~~ APPLICATION SERVER CODE ~~~~~~~~~~~~~~~~~~~


# Asks the server to return task mapping for the set of workers we provide,
# or return None if the workers fail to meet any additional qualifications
# or if there is no task ready to be completed
def get_assignment_task_map(waiting_assignments):
    # TODO: this should be moved into a separate module or become part of the application server
    return {
        # assignmentid : taskid
        u'1': 1
        #u'2': 1
    }


# Given a task id, return a json object that describes that task
def get_task_info(task_id):
    return {
        'task_id': 1,
        'photo_url': 'http://www.google.com',
    }


