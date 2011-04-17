from db_connection import DBConnection
from datetime import datetime
from timeutils import *
from padnums import pprint_table
import sys
import numpy

def parseVideos():
    """
    Grabs each video from the DB and tells us information
    about its lag
    """
    db = DBConnection()
    all_videos = db.query_and_return_array("""SELECT pk, filename FROM videos""")
    
    printPhaseTimes(db, all_videos)
    print('\n')
    printVideoTimes(db)
    
def printVideoTimes(db):
    result = db.query_and_return_array(
    """SELECT pictures.videoid, MIN(start), MAX(end), MAX(end) - MIN(start) AS elapsed FROM pictures, phase_lists, phases
    WHERE pictures.phase_list = phase_lists.pk
    AND phase_lists.pk = phases.phase_list
    AND phase_lists.is_historical = FALSE
    GROUP BY phase_lists.pk""")
    
    table = [["video", "elapsed"]]
    for picture in result:
        table.append([str(picture['videoid']), str(picture['elapsed'])])
        
    print("Median: %s" % numpy.median([float(row[1]) for row in table[1:]]))        
    pprint_table(sys.stdout, table)

def printPhaseTimes(db, all_videos):
    table = [["video", "phase list", "phase", "phase order", "width", "first go", "crowd go", "first ping", "crowd ping", "agreement", "total", "num workers", "on retainer"]]
    
    rows = []
    for video in all_videos:
        video_rows = parseVideo(video['pk'], db)
        rows.extend(video_rows)
    
    if len(rows) > 0:
        median_row = [ "median", "median", "median", "median" ]
        for column in range(4, len(rows[0])):
            numpy_data = filter(lambda x: x is not None, list(numpy.array(rows)[:,column]))
            medians = numpy.median(numpy.array([ numpy_data ]))
            median_row.append(medians)
        rows = [median_row] + rows
    
        for row in rows:
            table.append(map(stringOrNothing, row))
        
        pprint_table(sys.stdout, table)
    
def stringOrNothing(item):
    if item is None or item == numpy.nan:
        return ""
    else:
        return str(item)

def parseVideo(videoid, db):
    """
    Gets timing information for each video
    """

    video_rows = []
    
    phase_lists = db.query_and_return_array("""SELECT DISTINCT(phase_lists.pk) FROM phase_lists, phases, pictures WHERE phase_lists.pk = pictures.phase_list AND
    phase_lists.pk = phases.phase_list AND is_historical = FALSE AND phase_lists.videoid = %s""", (videoid,))
    
    for phase_list in phase_lists:
        phases = db.query_and_return_array("""SELECT *, COUNT(DISTINCT assignmentid) FROM phases, locations WHERE phases.phase_list = %s AND locations.phase = phases.phase GROUP BY phases.phase ORDER BY start""", (phase_list['pk'],))
    
        for (i, phase) in enumerate(phases):
            if phase['COUNT(DISTINCT assignmentid)'] < 2:
                print("WARNING: one of the photos is missing people. What's going on?\nWARNING\nWARNING\nWARNING\nWARNING\nWARNING")
                continue
        
            start = datetime.fromtimestamp(phase['start'])
            end = datetime.fromtimestamp(phase['end'])                    
        
            workers = db.query_and_return_array("""SELECT MIN(servertime), assignmentid FROM locations WHERE phase = %s GROUP BY assignmentid ORDER BY MIN(servertime)""", (phase['phase'],))
            
            first_ping = datetime.fromtimestamp(workers[0]['MIN(servertime)'])
            second_ping = datetime.fromtimestamp(workers[1]['MIN(servertime)'])
            
            retainers = db.query_and_return_array("""SELECT COUNT(DISTINCT assignmentid) FROM logging, phases WHERE event="ping-waiting" AND servertime >= (phases.start - 10) AND servertime <= phases.start AND phases.phase = %s""", (phase['phase'], ))[0]['COUNT(DISTINCT assignmentid)']
            
            assignments = db.query_and_return_array("""SELECT * FROM assignments, locations WHERE assignments.assignmentid = locations.assignmentid AND phase = %s AND `submit` IS NOT NULL GROUP BY assignments.assignmentid""", (phase['phase'], ))
            
            readies = sorted([datetime.fromtimestamp(row['go']) for row in assignments])
            shows = sorted([datetime.fromtimestamp(row['show']) for row in assignments])
            
            width = float(phase['max'] - phase['min'])
            
            if len(readies) < 2:
                continue
            
            if i==0:
                first_go = total_seconds(readies[0] - shows[0])
                crowd_go = total_seconds(readies[1] - shows[0])
                first_ping_wait = total_seconds(first_ping - shows[0])
                crowd_wait = total_seconds(second_ping - shows[0])                
                agreement = total_seconds(end - second_ping)
            else:
                first_go = None
                crowd_go = None
                first_ping_wait = None
                crowd_wait = None
                agreement = total_seconds(end - start)
            total = total_seconds(end - start)
            
            video_rows.append([videoid, phase_list['pk'], phase['phase'], i+1, width, first_go, crowd_go, first_ping_wait, crowd_wait, agreement, total, phase['COUNT(DISTINCT assignmentid)'], retainers])
    
    return video_rows

    
#     submit_deltas = []
#     for submission in submissions:
#         go_time = datetime.fromtimestamp(submission['go'])    
#         submit_time = datetime.fromtimestamp(submission['submit'])
#         
#         create_go = go_time - creation_time
#         go_submit = submit_time - creation_time
#         print('\t%s\t%s' % (total_seconds(create_go), total_seconds(go_submit)))
# 
#     pictures = db.query_and_return_array("""SELECT logging.assignmentid, servertime, go FROM logging, assignments WHERE logging.assignmentid = assignments.assignmentid AND videoid = %s AND event = 'picture' AND submit IS NOT NULL ORDER BY servertime ASC""", (videoid,) )
#     picture_times = []
#     for picture in pictures:
#         picture_time = datetime.fromtimestamp(picture['servertime'])
#         go_time = datetime.fromtimestamp(picture['go'])
#         
#         create_picture = total_seconds(picture_time - creation_time)
#         go_picture = total_seconds(picture_time - go_time)
#         picture_times.append(create_picture)
#     
#     picture_times.sort()
#     print(picture_times)
    
if __name__ == "__main__":
    parseVideos()
    
   
# Just asking people to take photos
"""
[11.813000000000001, 14.401, 15.945, 22.431000000000001, 25.640000000000001, 30.306999999999999, 56.494999999999997, 70.334000000000003, 71.611999999999995, 72.730999999999995, 74.932000000000002, 80.594999999999999, 82.271000000000001, 88.667000000000002, 89.668000000000006, 92.346000000000004, 103.66200000000001, 105.89, 109.97199999999999, 117.24299999999999, 117.524, 139.226, 160.59999999999999, 162.03999999999999, 163.404, 163.68199999999999, 187.358]
"""

# how long does it take for each picture to complete?    
"""
SELECT pictures.videoid, pictures.phase_list, MIN(start), MAX(end), MAX(end) - MIN(start) AS elapsed FROM pictures, phase_lists, phases
WHERE pictures.phase_list = phase_lists.pk
AND phase_lists.pk = phases.phase_list
AND phase_lists.is_historical = FALSE
GROUP BY phase_lists.pk
"""

# how long was each phase?
"""
SELECT *, end - start, COUNT(DISTINCT assignmentid) FROM pictures, phase_lists, phases, locations WHERE phase_lists.pk = pictures.phase_list AND phases.phase_list = phase_lists.pk AND locations.phase = phases.phase AND is_historical = FALSE GROUP BY phases.phase
"""

# how long were they waiting in that long phase?
"""
SELECT (end - MIN(servertime)) FROM locations, phases, phase_lists, pictures WHERE phases.phase_list=phase_lists.pk AND phases.phase = locations.phase AND pictures.phase_list = phase_lists.pk GROUP BY pictures.pk, assignmentid
"""