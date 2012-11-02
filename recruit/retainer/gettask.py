from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max

import json
import simplejson

from retainer.models import *
from retainer.ping import PING_TYPES
from retainer.utils.transaction import flush_transaction

from datetime import datetime, timedelta
from retainer.utils.timeutils import unixtime

from settings import MIN_WAITING_WORKERS, PING_TIMEOUT_SECONDS

# Get a task for the worker, or assign one if we can
@csrf_exempt
def get_task(request, assignment_id):
    # find out whether the worker has already been assigned a task. if so, just return that task.
    current_assignments = Assignment.objects.filter(assignment_id = assignment_id)
    waiting_assignments = waiting_workers()
    current = current_assignments[0] if len(current_assignments) > 0 else None
    if current is None:
        return HttpResponse('Bad assignment')
    if current.task_id is not None:
        task_info = { 'start': True, 'task_id': int(current.task_id) }
    else:
        proto = current.hit_id.proto
        work_reqs = WorkRequest.objects.filter(proto=proto, done=False).order_by('-id')
                
        if len(work_reqs) > 0:
            tid = work_reqs[0].foreign_id
            current.task_id = tid
            task_info = { 'start': True, 'task_id': int(tid)}
            current.save()
        else:
            task_info = { 'start': False }

    # now turn the task_info python into JSON to return to the client
    return HttpResponse(simplejson.dumps(task_info), mimetype="application/json")


# Return the number of workers who are waiting on retainer right now
def waiting_workers():
    flush_transaction()
    time_ping_floor = datetime.now() - timedelta(seconds = PING_TIMEOUT_SECONDS)

    waiting_assignments = Assignment.objects.filter(event__event_type = PING_TYPES['waiting'], event__server_time__gte = unixtime(time_ping_floor), task_id = None).distinct()
    return waiting_assignments


def save_assignment_task_map(assignment_map):
    for assignment_id in assignment_map.keys():
        task_id = assignment_map[assignment_id]
        assignment = Assignment.objects.get(assignment_id = assignment_id)
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



