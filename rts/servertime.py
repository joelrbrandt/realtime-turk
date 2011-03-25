from datetime import datetime
import simplejson as json
from rtsutils.timeutils import *

def servertime(request):
    now = round(unixtime(datetime.now()) * 1000) # javascript uses millis, not seconds
    request.content_type = "application/json"
    request.write(json.dumps({'date': now }))
    
