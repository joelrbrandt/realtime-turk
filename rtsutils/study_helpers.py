from db_connection import DBConnection
import json

from rtsutils.parseresults import groupAssignmentsByKey

from decimal import Decimal 

NUM_VIDEOS = 72
VOTES_TO_WIN = 3

CONTINUOUS_REFINEMENT = 'refinement'
GENERATE_AND_VOTE = 'generate-vote'
GENERATE_FIRST = 'generate-first'
PHOTOGRAPHER = 'photographer'

def deleteContinuousRefinement():
    db = DBConnection()
    db.query_and_return_array("DELETE FROM algorithms WHERE algorithm = %s", (CONTINUOUS_REFINEMENT))
    print("Deleted")

def portContinuousRefinement():
    """ports information into the algorithhms table for the continuous refinement condition"""
    db = DBConnection()
    sql = """SELECT * FROM pictures, study_videos, phase_lists WHERE pictures.videoid = study_videos.videoid AND pictures.phase_list = phase_lists.pk AND NOT is_historical GROUP BY pictures.videoid"""
    pictures = db.query_and_return_array(sql)
    
    if len(pictures) != NUM_VIDEOS:
        print(str(len(pictures)) + " videos instead of " + str(NUM_VIDEOS) + ". Stopping.")
        print([picture['videoid'] for picture in pictures])
        return

    for picture in pictures:
        sql = """INSERT INTO algorithms (algorithm, videoid, location, detail) VALUES (%s, %s, %s, %s)"""
        detail = json.dumps(dict( phase_list = picture['phase_list'] ))
        db.query_and_return_array(sql, (CONTINUOUS_REFINEMENT, picture['videoid'], picture['location'], detail))
    
    print("done")
    
def portGenerateAndVote():
    """ports information into the algorithms table for the generate and vote condition"""
    
    db = DBConnection()
    sql = """SELECT vote_assignments.pk, study_videos.videoid, vote FROM study_videos
        LEFT JOIN (SELECT slow_votes.pk, slow_votes.assignmentid, videoid, vote FROM slow_votes, assignments WHERE slow_votes.assignmentid = assignments.assignmentid) AS vote_assignments 
        ON vote_assignments.videoid = study_videos.videoid 
    WHERE slow_voting_available = TRUE ORDER BY vote_assignments.pk"""
    
    votes = db.query_and_return_array(sql)
    # we need to take just the first five votes for each video
    grouped_votes = groupAssignmentsByKey(votes, lambda x: x['videoid'])
    videoids = sorted(grouped_votes.keys())
    
    votes = []
    for videoid in videoids:
        video_votes = sorted(list(grouped_votes[videoid]), key=lambda x: x['pk'])
        
        num_votes = 0
        winner = None
        while winner is None:
            if len(video_votes) < num_votes:
                print("Not enough votes to decide this case: %s", video_votes)
                return
                
            num_votes += 1        
            (winner, counts) = checkForWinner(video_votes[:num_votes])
        
        vote = dict()
        vote['videoid'] = videoid
        vote['slow_vote_pks'] = [vote['pk'] for vote in video_votes[:num_votes]]
        vote['count'] = counts
        vote['winner'] = (Decimal(str(winner)) / 100) - Decimal('.01') # off by one frame error from jpeg filename to slider position
        
        votes.append(vote)
        print vote
    
    # num_voters = sorted([len(vote['slow_vote_pks']) for vote in votes])
    for vote in votes:
        db.query_and_return_array("""INSERT INTO algorithms (algorithm, videoid, location, detail) VALUES (%s, %s, %s, %s)""", (GENERATE_AND_VOTE, vote['videoid'], vote['winner'], json.dumps(vote, cls = StudyDecimalEncoder)))
    print("Done")


def portTakeFirst():
    db = DBConnection()
    sql = """SELECT slow_snapshots.pk, slow_snapshots.location, assignments.videoid FROM slow_snapshots, assignments WHERE slow_snapshots.pk IN

        (SELECT MIN(slow_snapshots.pk) FROM slow_snapshots, assignments, study_videos WHERE assignments.assignmentid = slow_snapshots.assignmentid AND assignments.videoid = study_videos.videoid AND workerid NOT LIKE 'photographer' GROUP BY study_videos.videoid) 

    AND assignments.assignmentid = slow_snapshots.assignmentid ORDER BY assignments.videoid ASC
    """
    
    snapshots = db.query_and_return_array(sql)
    for snapshot in snapshots:
        print(snapshot)
        db.query_and_return_array("""INSERT INTO algorithms (algorithm, videoid, location, detail) VALUES (%s, %s, %s, %s)""", (GENERATE_FIRST, snapshot['videoid'], snapshot['location'], json.dumps( dict( snapshot_pk = snapshot['pk'] ) )))
    print("Done!")
    
    
def portPhotographer():
    db = DBConnection()
    snapshots = db.query_and_return_array("""SELECT slow_snapshots.pk, slow_snapshots.location, assignments.videoid
    FROM slow_snapshots, assignments, study_videos WHERE    slow_snapshots.assignmentid = assignments.assignmentid AND workerid LIKE 'photographer' AND study_videos.videoid = assignments.videoid ORDER BY assignments.videoid""")
    
    for snapshot in snapshots:
        print(snapshot)
        db.query_and_return_array("""INSERT INTO algorithms (algorithm, videoid, location, detail) VALUES (%s, %s, %s, %s)""", (PHOTOGRAPHER, snapshot['videoid'], snapshot['location'], json.dumps( dict( snapshot_pk = snapshot['pk'] ) )))
    print("Done!")


def checkForWinner(votes):
    counts = dict()
    for vote in votes:
        if not counts.has_key(vote['vote']):
            counts[vote['vote']] = 0
        counts[vote['vote']] += 1
        
    most_votes = None
    for candidate in counts.keys():
        if most_votes is None or counts[most_votes] < counts[candidate]:
            most_votes = candidate

    if counts[most_votes] >= VOTES_TO_WIN:
        return (most_votes, counts)
    else:
        return (None, counts)
        
# TODO: abstract out to separate file and remove location_ping.DecimalEncoder
class StudyDecimalEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return (str(o) for o in [o])
        return super(StudyDecimalEncoder, self)._iterencode(o, markers)
        