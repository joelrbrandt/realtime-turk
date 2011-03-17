import MySQLdb
import simplejson as json
import settings

""" Major inputs: text id and string list of verb indices in text"""
text_id = 1 # text id in database
json_groundtruth = "[2, 4, 19, 20, 26, 36, 38, 45, 53, 58, 76, 78, 87, 89, 101, 103, 107, 116, 118, 120, 122]" # get by calling getSelectedVerbs() in javascript

def main():
    ground_truth_array = json.loads(json_groundtruth)
    setGroundTruth(text_id, ground_truth_array)

def setGroundTruth(text_id, ground_truth_array):
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    zipped = zip([text_id] * len(ground_truth_array), ground_truth_array)
    print(zipped)
    
    cur.executemany("""INSERT INTO groundtruth (textid, wordid) VALUES (%s, %s)""", zipped)
    cur.close()
    db.close()

main()