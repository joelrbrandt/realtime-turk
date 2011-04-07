from db_connection import DBConnection
from datetime import datetime
from timeutils import *

def parseVideos():
    """
    Grabs each video from the DB and tells us information
    about its lag
    """
    db = DBConnection()
    all_videos = db.query_and_return_array("""SELECT pk, filename, creationtime FROM videos""")
    for video in all_videos:
        print("Video: %s" % (video['filename']))
    
        creation_time = datetime.fromtimestamp(video['creationtime'])
        parseVideo(video['pk'], creation_time, db)

def parseVideo(videoid, creation_time, db):
    """
    Gets timing information for each video
    """
    
    submissions = db.query_and_return_array("""SELECT go, submit FROM assignments WHERE videoid = %s AND submit IS NOT NULL ORDER BY submit""", (videoid,))
    
    submit_deltas = []
    for submission in submissions:
        go_time = datetime.fromtimestamp(submission['go'])    
        submit_time = datetime.fromtimestamp(submission['submit'])
        
        create_go = go_time - creation_time
        go_submit = submit_time - creation_time
        print('\t%s\t%s' % (total_seconds(create_go), total_seconds(go_submit)))

    pictures = db.query_and_return_array("""SELECT logging.assignmentid, servertime, go FROM logging, assignments WHERE logging.assignmentid = assignments.assignmentid AND videoid = %s AND event = 'picture' AND submit IS NOT NULL ORDER BY servertime ASC""", (videoid,) )
    picture_times = []
    for picture in pictures:
        picture_time = datetime.fromtimestamp(picture['servertime'])
        go_time = datetime.fromtimestamp(picture['go'])
        
        create_picture = total_seconds(picture_time - creation_time)
        go_picture = total_seconds(picture_time - go_time)
        picture_times.append(create_picture)
    
    picture_times.sort()
    print(picture_times)
    
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
GROUP BY phase_lists.pk
"""

# how long was each phase?
"""
SELECT *, end - start FROM pictures, phase_lists, phases WHERE pictures.videoid = 17 AND phase_lists.pk = pictures.phase_list AND phases.phase_list = phase_lists.pk
"""

# how long were they waiting in that long phase?
"""
SELECT (end - MIN(servertime)) FROM locations, phases WHERE phases.phase=258 AND phases.phase = locations.phase GROUP BY assignmentid
"""