from django.http import HttpResponse
import json
from django.db.models import Max
from retainer.models import *
from retainer.ping import PING_TYPES

from datetime import datetime, timedelta
from retainer.utils.timeutils import unixtime

from settings import MIN_WAITING_WORKERS, PING_TIMEOUT_SECONDS

# Get a task for the worker, or assign one if we can
def get_task(request, assignment_id):
    # find out whether the worker has already been assigned a task. if so, just return that task.
    current_assignments = Assignments.objects.filter(assignment_id = assignment_id)
    if len(current_assignments) > 0 and current_assignments[0].task_id is not None:
        task_info = get_task_info(current_assignments[0].task_id)

    else:
        # are there enough workers waiting?
        # if so, ask the application server to give us a task to do, or to decline giving a task
        waiting_assignments = waiting_workers()
        if len(waiting_assignments) >= MIN_WAITING_WORKERS:
            assignment_map = get_assignment_task_map(waiting_assignments)
            save_assignment_task_map(assignment_map)
        
            # now we get the current worker's task out of that map and return it to the client
            current_worker_task = assignment_map[assignment_id]
            task_info = get_task_info(current_worker_task)
        else:
            # not enough workers, return no job
            task_info = { 'task_id': None }

    # now turn the task_info python into JSON to return to the client
    serialized = json.dumps(task_info)
    return HttpResponse(serialized, mimetype="application/json")


# Return the number of workers who are waiting on retainer right now
def waiting_workers():
    time_ping_floor = datetime.now() - timedelta(seconds = PING_TIMEOUT_SECONDS)

    waiting_assignments = Assignments.objects.filter(events__event_type = PING_TYPES['waiting'], events__server_time__gte = unixtime(time_ping_floor), task_id = None).distinct()
    print(waiting_assignments)
    return waiting_assignments


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
    output = dict()
    for assignment in waiting_assignments:
        output[assignment.assignment_id] = 1 # assign to HIT 1, why not
    return output


# Given a task id, return a json object that describes that task
def get_task_info(task_id):
    return {
        'task_id': task_id,
        'photo_url': 'http://www.google.com',
    }


