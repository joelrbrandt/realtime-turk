from mod_python import apache, util
from rtsutils.db_connection import DBConnection
import random
import simplejson as json

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
    

def getImages(db, is_good):
    images = db.query_and_return_array("""SELECT filename FROM verification WHERE is_good = %s""", (is_good, ))
    return [row['filename'] for row in images]
