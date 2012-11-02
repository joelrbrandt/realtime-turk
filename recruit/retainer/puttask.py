from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import simplejson
from retainer.models import *

@csrf_exempt
def put_task(request):
    if request.method == 'POST':
        params = request.POST
        if 'api_key' in params and 'json' in params:
            if not APIKey.check(params['api_key']):
                return HttpResponse('Denied.')
            # now, add stuff from json into a ProtoHit
            json = simplejson.loads(params['json'])
            ph = ProtoHit(hit_type_id = json['hit_type_id'], 
                    title=json['title'], 
                    description=json['description'], 
                    keywords=json['keywords'], 
                    url=json['url'], 
                    reward=float(json['reward']), 
                    assignment_duration=int(json['assignment_duration']), 
                    lifetime=int(json['lifetime']),
                    max_assignments=int(json['max_assignments']),
                    auto_approval_delay=int(json['auto_approval_delay']),
                    worker_locale=json['worker_locale'],
                    approval_rating=int(json['approval_rating']),
                    retainertime=int(json['retainertime']))
            ph.save()
            return HttpResponse(str(ph.id))
        return HttpResponse('OK')
    elif request.method == 'GET':
        return HttpResponse('Bad request type.')