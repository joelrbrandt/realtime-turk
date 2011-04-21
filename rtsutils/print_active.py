import settings
from rtsutils import condition
from rtsutils.word_clicker_approver import RECALL_LIMIT, PRECISION_LIMIT

from db_connection import DBConnection
from datetime import datetime, timedelta
import simplejson as json
from rtsutils.timeutils import *

import numpy
from scipy import stats, interpolate
from matplotlib import pyplot
import scikits.statsmodels

from padnums import pprint_table
import sys
from itertools import groupby

def printCurrentlyActiveCount():
    ping_floor = datetime.now() - timedelta(seconds = 15)
    ping_types = ["ping-waiting", "ping-showing", "ping-working"]

    db = DBConnection()

    results = dict()
    for ping_type in ping_types:
    
        row = db.query_and_return_array("""SELECT COUNT(DISTINCT assignmentid) FROM logging WHERE event='%s' AND servertime >= %s""" % ( ping_type, unixtime(ping_floor) ))[0]
        results[ping_type] = row['COUNT(DISTINCT assignmentid)']

        print(ping_type + ": unique assignmentIds pings in last 15 seconds: " + str(results[ping_type]))
    return results


if __name__ == "__main__":
    printCurrentlyActiveCount()
