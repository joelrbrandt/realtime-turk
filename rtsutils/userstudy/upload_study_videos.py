import video_poster, video_encoder
from db_connection import DBConnection

 # just use video_posert.postVideo in a loop until nothing remains to post
 
"""
import os, shutil

DIRECTORY_RANGE = range(1, 13)

def uploadStudyVideos():
    db = DBConnection()
    original_directory = video_poster.VIDEO_DIRECTORY
    for i in DIRECTORY_RANGE:
        #video_poster.VIDEO_DIRECTORY = original_directory + str(i) + '/'
        try:
            os.mkdir(video_poster.VIDEO_DIRECTORY + 'flv')
            os.mkdir(video_poster.VIDEO_DIRECTORY + 'jpg')
        except OSError:
            print("Directory exists")
            
        directory = video_poster.VIDEO_DIRECTORY + str(i) + '/'
        dirList = os.listdir(directory)            
        in_directory = filter(lambda x: x.endswith('.3gp'), dirList)        
        for videofile in in_directory:
            video_poster.encodeAndUpload(directory + videofile)
            shutil.copyfile(directory+'flv/' + videofile, 
"""            
    
if __name__ == "__main__":
    uploadStudyVideos()