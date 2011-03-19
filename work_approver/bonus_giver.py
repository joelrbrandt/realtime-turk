from boto.mturk import connection
import MySQLdb
import MySQLdb.cursors

import logging
import sys
from optparse import OptionParser

import settings

def approve_and_bonus_assignment(conn, hit_id, worker_id, assignment_id, bonus_amount, reason):
    """
    returns True if was able to successfully give a bonus, False otherwise

    Note: This code may not work correctly if there are more than 100 assignments per hit.
    Right now, our qturk code uses 2 assignments per hit.
    """

    result = False
    assignments = []

    try:
        assignments = conn.get_assignments(hit_id, page_size=100)
    except:
        logging.exception("Got exception trying to get assignments for HIT ID: " + str(hit_id))

    for a in assignments:
        if a.AssignmentId == assignment_id and a.WorkerId == worker_id:
            try:
                # TODO: Here is where we could add code to approve/reject based on quality
                if a.AssignmentStatus == "Submitted":
                    conn.approve_assignment(assignment_id, feedback=reason)
                    logging.info("successfully approved assignment with Assignment ID: " + str(assignment_id))
                else:
                    logging.warning("assignment already reviewed, will grant (another) bonus. Assignment ID: " + str(assignment_id))

                if a.AssignmentStatus == "Submitted" or a.AssignmentStatus == "Approved": # don't give bonus if rejected
                    conn.grant_bonus(worker_id, assignment_id, conn.get_price_as_price(bonus_amount), reason)
                    logging.info("successfully granted bonus for Assignment ID: " + str(assignment_id))
                else:
                    logging.info("skipped granting bonus because assignment wasn't in 'submitted' or 'approved' state. Assignment ID: " + str(assignment_id))

                result = True
                break
            except:
                logging.exception("Got exception trying to approve and grant bonus to Assignment ID: " + str(assignment_id))

    return result

def get_assignments_to_bonus(db_conn):
    """
    returns all assignments in the db that need a bonus, or an empty array if there is an error
    """
    r = []
    try:
        cur = db_conn.cursor()
        cur.execute("SELECT * FROM `bonuses` WHERE give_bonus=1 AND bonus_paid=0")
        r = cur.fetchall()
    except:
        logging.exception("Got exception trying to get assignments from the db")
    return r

def mark_assignment_as_bonus_paid(db_conn, assignment_id):
    """
    returns True if the bonus payment was successfully marked in the DB, False otherwise.
    """
    result = False
    try:
        cur = db_conn.cursor()
        cur.execute("UPDATE `bonuses` SET bonus_paid=1 WHERE assignment_id=%s", (str(assignment_id)))
        logging.info("successfully marked db entry as paid for Assignment ID: " + str(assignment_id))
        result = True
    except:
        logging.exception("Got exception trying to mark db entry as paid for Assignment ID: " + str(assignment_id))
    return result

def get_db_conn():
    """
    returns a connection to the database
    requires that settings defines the following variables:
    
    settings.DB_USER:        username
    settings.DB_PASSWORD:    password
    settings.DB_HOST:        hostname
    settings.DB_DATABASE:    database name
    """

    return MySQLdb.connect(host=settings.DB_HOST,
                           passwd=settings.DB_PASSWORD,
                           user=settings.DB_USER,
                           db=settings.DB_DATABASE,
                           cursorclass=MySQLdb.cursors.DictCursor,
                           use_unicode=True)
            
def get_mt_conn(sandbox=settings.SANDBOX):
    """
    returns a connection to mechanical turk.
    requires that settings defines the following variables:
    
    settings.SANDBOX:    True|False
    settings.aws_id:     your aws id
    settings.aws_secret: your aws secret key
    """
    if sandbox:
        host="mechanicalturk.sandbox.amazonaws.com"
    else:
        host="mechanicalturk.amazonaws.com"

    return connection.MTurkConnection(
        aws_access_key_id=settings.aws_id,
        aws_secret_access_key=settings.aws_secret,
        host=host)
    
def grant_all_pending_bonuses():
    """
    Main function that loops through all pending bonuses in the DB and grants them
    """
    mt_conn = get_mt_conn()
    db_conn = get_db_conn()

    if mt_conn != None and db_conn != None:
        assignments = get_assignments_to_bonus(db_conn)
        logging.info("Got " + str(len(assignments)) + " from the database")
        for a in assignments:
            logging.info("Processing assignment with ID " + str(a['assignment_id']))
            if approve_and_bonus_assignment(mt_conn, a['hit_id'], a['worker_id'], a['assignment_id'], settings.bonus_amount, settings.bonus_reason):
                mark_assignment_as_bonus_paid(db_conn, a['assignment_id'])
            
if __name__ == "__main__":
    # Parse the options
    parser = OptionParser()
    parser.add_option("-l", "--log", dest="logfile", help="log to FILE", metavar="FILE")
    (options, args) = parser.parse_args()
    if options.logfile:
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s',
                            filename=options.logfile,
                            filemode='w')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s',
                            stream=sys.stdout)

    # Do the real work

    grant_all_pending_bonuses()
