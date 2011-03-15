import os
from datetime import datetime, timedelta
import time

def parseISO(input):
    split_dt = input.split('.')
    no_millis = datetime.strptime( split_dt[0], "%Y-%m-%dT%H:%M:%S" )
    millis = int(split_dt[1][:-1])  # remove the 'Z' at the end
    
    final_date = no_millis + timedelta(milliseconds = millis)
    
    return unixtime(final_date)

def unixtime(dt):
    millis = dt.microsecond/1000000.
    return time.mktime(dt.timetuple()) + millis    
    
os.environ['TZ'] = 'America/NewYork'
time.tzset()