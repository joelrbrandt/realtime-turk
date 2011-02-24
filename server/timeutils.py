import os
from datetime import datetime
import time

def parseISO(input):
    basic = datetime.strptime( input, "%Y-%m-%dT%H:%M:%S.%fZ" )
    return unixtime(basic)

def unixtime(dt):
    millis = dt.microsecond/1000000.
    return time.mktime(dt.timetuple()) + millis    
    
os.environ['TZ'] = 'America/NewYork'
time.tzset()