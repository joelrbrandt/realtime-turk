import time
import video_approver, vote_approver

SLEEP_TIME = 5 * 60

def approveLoop():
    while True:
        print("Wake up")
        video_approver.approve_video_hits_and_clean_up(verbose=True, dry_run=False)
        vote_approver.approve_vote_hits_and_clean_up(verbose=True, dry_run=False)        
        print("Go to sleep for %s" % SLEEP_TIME)
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    approveLoop()