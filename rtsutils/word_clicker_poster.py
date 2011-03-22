from optparse import OptionParser

from word_clicker_hit import *
from db_connection import *
from mt_connection import *

"""
    if options.logfile:
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s',
                            filename=options.logfile,
                            filemode='w')
    else:
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s',
"""

EXPERIMENT_NUMBER = 40

if __name__ == "__main__":
    # Parse the options
    parser = OptionParser()
    parser.add_option("-e", "--experiment-number", dest="experiment_number", help="EXPERIMENT number", metavar="EXPERIMENT")
    parser.add_option("-n", "--number-of-hits", dest="number_of_hits", help="NUMBER of hits", metavar="NUMBER")
    parser.add_option("-b", "--wait-bucket", dest="waitbucket", help="number of SECONDS to wait on retainer", metavar="SECONDS")
    parser.add_option("-p", "--price", dest="price", help="number of CENTS to pay", metavar="CENTS")

    (options, args) = parser.parse_args()

    n = int(options.number_of_hits)
    b = int(options.waitbucket)
    e = int(options.experiment_number)
    p = int(options.price)/100.0


    c = get_mt_conn()
    d = DBConnection()
    h = WordClickerHit(e, 
                       waitbucket=b,
                       reward_as_usd_float=p,
                       assignment_duration=b+120,
                       lifetime=10*60)

    for i in range(n):
        try:
            hit = h.post(c,d)
            print "Posted HIT ID " + hit.HITId
        except Exception, e:
            print "Got exception posting HIT:\n" + str(e)
