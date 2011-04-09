from mod_python import apache, util
from rtsutils.db_connection import DBConnection
import random
import json
from rtsutils.video_approver import getImages

def getValidationImages(request):
    db = DBConnection()
    good = getImages(db, True)
    bad = getImages(db, False)
    
    videos = []
    videos.append(random.choice(good))
    videos.append(random.choice(bad))
    videos.append(random.choice(bad))
    
    random.shuffle(videos)
    request.write(json.dumps(videos))