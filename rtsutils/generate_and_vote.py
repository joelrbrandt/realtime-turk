from db_connection import DBConnection
import numpy

def generateAndVote():
    db = DBConnection()
    generate = db.query_and_return_array("""SELECT * FROM assignments, slow_snapshots, study_videos 
    WHERE
    assignments.assignmentid = slow_snapshots.assignmentid
    AND assignments.videoid = study_videos.videoid
    AND workerid NOT LIKE 'photographer'
    ORDER BY assignments.videoid, assignments.submit""")
    generate_by_video = groupByKey(generate, lambda x: x['videoid'])
    
    lags = []
    
    for video in generate_by_video.keys():
        print(video)
        generates = list(generate_by_video[video])
        # get third dude
        third = generates[2]
        generate_lag = third['submit'] - third['slow_available_time']
        #print generate_lag
        
        votes = db.query_and_return_array("""SELECT * FROM assignments,
        slow_votes, study_videos WHERE assignments.videoid = %s AND assignments.assignmentid = slow_votes.assignmentid AND assignments.videoid = study_videos.videoid ORDER BY assignments.submit""", (video, ))
        fifth = votes[4]
        vote_lag = fifth['submit'] - fifth['slow_voting_available_time']
        #print vote_lag
        lags.append(float(generate_lag + vote_lag))
        print(lags[-1])
        
    print lags
    
    print("\n\n\nRESULTS")
    print("Median: %s" % numpy.median(lags))
    print("Average: %s" % numpy.mean(lags))    
    print("Std. Dev: %s" % numpy.std(lags))    

def groupByKey(assignments, key):
    """Splits  into groups based on their key. Returns a dict from condition to list of assignments"""
    group_assignments = dict()

    all_groups = set([key(assignment) for assignment in assignments])
    for group in all_groups:
        filtered_assignments = filter(lambda assignment: key(assignment) == group, assignments)
        group_assignments[group] = filtered_assignments
    
    return group_assignments

if __name__=="__main__":
    generateAndVote()