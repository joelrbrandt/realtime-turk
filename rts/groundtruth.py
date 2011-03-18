import MySQLdb
import simplejson as json
import settings

""" Major inputs: text id and string list of verb indices in text"""
text_id = 25 # text id in database
# get by calling getSelectedVerbs() in javascript
json_groundtruth = "[1, 3, 5, 8, 15, 22, 48, 58, 67, 75, 85]"

def main():
    ground_truth_array = json.loads(json_groundtruth)
    setGroundTruth(text_id, ground_truth_array)

def setGroundTruth(text_id, ground_truth_array):
    db=MySQLdb.connect(host=settings.DB_HOST, passwd=settings.DB_PASSWORD, user=settings.DB_USER, db=settings.DB_DATABASE, use_unicode=True)
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    
    zipped = zip([text_id] * len(ground_truth_array), ground_truth_array)
    print(zipped)
    
    cur.execute("""DELETE FROM groundtruth WHERE textid = %s""", (text_id,))
    cur.executemany("""INSERT INTO groundtruth (textid, wordid) VALUES (%s, %s)""", zipped)
    cur.close()
    db.close()

main()