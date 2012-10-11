from django.http import HttpResponse
from retainer.models import *

from datetime import datetime, timedelta
from retainer.utils.timeutils import unixtime

PING_TYPES = {
    'waiting': 'waiting',
    'working': 'working',
    'showing': 'alerting',
}

def ping(request, worker_id, assignment_id, hit_id, ping_type):
    assignment = get_assignment(assignment_id, worker_id, hit_id)

    ping = PING_TYPES[ping_type]
    event = Events(assignment = assignment, event_type = ping,
                   ip = request.META['REMOTE_ADDR'],
                   user_agent = request.META['HTTP_USER_AGENT'],
                   server_time = unixtime(datetime.now()),
                   client_time = 0, # TODO: fix. add to url params or switch to POST
                   detail = '')
    event.save()

    return HttpResponse('OK')
                                      
def get_assignment(assignment_id, worker_id, hit_id):
    hit = Hits.objects.get(hit_id = hit_id)
    assignment = None

    # get the assignment information
    try:
        assignment = Assignments.objects.get(assignment_id = assignment_id)
        # if necessary, update the assignment to the current hit and worker
        if assignment.worker_id != worker_id or assignment.hit_id != hit:
            assignment.hit_id = hit
            assignment.worker_id = worker_id
            assignment.save()

    except Assignments.DoesNotExist:
        assignment = Assignments(assignment_id = assignment_id, worker_id = worker_id, hit_id = hit)
        assignment.save()

    return assignment
