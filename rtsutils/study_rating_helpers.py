from db_connection import DBConnection

db = DBConnection()

def parse_participant_number(username):
    result = None
    try:
        result = int(username[1:])
    except:
        pass # malformed username, so guess we'll bail
    return result

def get_all_algorithm_ids_for_participant(participant_number):
    algorithm_ids = set()
    photo_groups = get_photos_to_rate(participant_number)
    for g in photo_groups.values():
        for p in g:
            algorithm_ids.add(p["id"])
    return algorithm_ids

def get_all_ratings_for_participant(participant_number):
    ids = get_all_algorithm_ids_for_participant(participant_number)
    ratings = {}
    temp_ratings = []
    for i in ids:
        temp_ratings.extend(db.query_and_return_array("SELECT * FROM study_ratings WHERE algorithmid = %s", (str(i),)))
    for r in temp_ratings:
        ratings[r['algorithmid']] = r

    return ratings

def check_all_rated(participant_number):
    algorithm_ids = get_all_algorithm_ids_for_participant(participant_number)
    ratings = get_all_ratings_for_participant(participant_number)
    rated_ids = set(ratings.keys())
    left_to_rate = algorithm_ids - rated_ids
    return len(left_to_rate) == 0


def record_ratings(participant_number, fieldstorage):
    recorded = {}
    algorithm_ids = get_all_algorithm_ids_for_participant(participant_number)
    for i in algorithm_ids:
        if fieldstorage.has_key("rating-" + str(i)):
            try:
                r = fieldstorage.getfirst("rating-" + str(i), 0)
                r_int = int(r)
                if not (r_int >= 1 and r_int <= 9):
                    raise Exception("rating not in rage")
                db.query_and_return_array("INSERT INTO study_ratings (algorithmid, rating) VALUES (%s, %s) ON DUPLICATE KEY UPDATE rating=%s", (i, r_int, r_int))
                recorded["rating-" + str(i)] = r_int
            except:
                pass # error parsing, so let's just go on

        if fieldstorage.has_key("comment-" + str(i)):
            try:
                c = fieldstorage.getfirst("comment-" + str(i), "")
                if len(c) == 0:
                    raise Exception("rating not in rage")
                db.query_and_return_array("INSERT INTO study_ratings (algorithmid, comment) VALUES (%s, %s) ON DUPLICATE KEY UPDATE comment=%s", (i, c, c))
                recorded["comment-" + str(i)] = c
            except:
                pass # error parsing, so let's just go on
    return recorded

    


def get_photos_to_rate(participant_number):
    """
    Returns a dict with entries the form:
      key: integer video id
      value: list of photo dicts
    (there should be three of these entires, given our study design)

    Each list of photos contains dicts defining the properties of each photo to be rated.
    The photo dicts look like this:
      { "id": primary key from algorithms table
        "videoid": primary key of the video the photo is from (from videos table)
        "location:" value in [0,1] of point in the video where the frame is 
        "frame:" frame number (computed in SQL so we don't lose any accuracy from Double representation)
        "filename:" complete filename of the image file (also computed in SQL)
        "alogrithm:" algorithm used to select the frame
        "participant_number": participant's number
      }
    
    """

    result = {}

    sql = """
SELECT
  algorithms.pk `id`,
  algorithms.videoid `videoid`,
  algorithms.location `location`,
  LEAST(FLOOR(algorithms.location*100 + 1), 100) as `frame`,
  CONCAT(videos.`filename`, LPAD(LEAST(FLOOR(algorithms.location*100 + 1), 100), 3, "0"), ".jpg") `filename`,
  algorithms.algorithm `algorithm`,
  study_videos.participant_number `participant_number`

FROM `algorithms`, `videos`, `study_videos`

WHERE
  algorithms.videoid = videos.pk AND study_videos.videoid = videos.pk
  AND study_videos.participant_number = %s
"""
    r = db.query_and_return_array(sql, (participant_number,))

    for e in r:
        if not result.has_key(e["videoid"]):
            result[e["videoid"]] = []
        result[e["videoid"]].append(e)

    return result
