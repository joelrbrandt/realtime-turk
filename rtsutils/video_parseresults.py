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