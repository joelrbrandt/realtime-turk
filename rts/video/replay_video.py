from mod_python import apache, util
import json

from rts import rts_logging
import logging
import location_ping
from rtsutils.timeutils import unixtime

from rtsutils.db_connection import DBConnection
from datetime import datetime, timedelta

def replayLog(request):
    request.content_type = "application/json"
    form = util.FieldStorage(request)
    videoid = form['videoid'].value
    
    db = DBConnection()
    phases = db.query_and_return_array("""SELECT * FROM phases, 
                (SELECT phase_lists.pk AS phase_list FROM
                phase_lists, pictures
                WHERE phase_lists.videoid = %s AND phase_lists.is_historical = FALSE AND phase_lists.pk = pictures.phase_list ORDER BY phase_lists.pk DESC LIMIT 1) AS pl WHERE phases.phase_list = pl.phase_list ORDER BY phase""", (videoid, ))
    
    for phase in phases:
        locations = db.query_and_return_array("""SELECT location, servertime, assignmentid, phase
                FROM locations WHERE phase = %s ORDER BY servertime""", (phase['phase'], ))
        phase['locations'] = locations
    
    request.write(json.dumps(phases, cls = location_ping.DecimalEncoder))

def getCurrentPositions(request):
    request.content_type = "application/json"
    form = util.FieldStorage(request)
    videoid = form['videoid'].value
    
    db = DBConnection()
    cur_phase = db.query_and_return_array("""SELECT * FROM phases, phase_lists
                WHERE phase_lists.videoid = %s AND phase_lists.pk = phases.phase_list
                ORDER BY phases.phase DESC LIMIT 1""", (videoid, ))[0]

    locations = db.query_and_return_array("""
                   SELECT locations.assignmentid, locations.location
                   FROM (
                      SELECT assignmentid, MAX(servertime) as maxtime
                      FROM locations WHERE phase = %s
                      GROUP BY assignmentid
                   ) AS current, locations WHERE current.maxtime = locations.servertime
                   AND current.assignmentid = locations.assignmentid AND locations.phase = %s
                   """, (cur_phase['phase'], cur_phase['phase'] ))

    cur_phase['locations'] = locations
    request.write(json.dumps(cur_phase, cls = location_ping.DecimalEncoder))
    
    
