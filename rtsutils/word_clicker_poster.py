from word_clicker_hit import *
from db_connection import *
from mt_connection import *

EXPERIMENT_NUMBER = 40

if __name__ == "__main__":
    h = WordClickerHit(EXPERIMENT_NUMBER)
    c = get_mt_conn()
    d = DBConnection()
    hit = h.post(c,d)
    print "Posted HIT ID " + hit.HITId

