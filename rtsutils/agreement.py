from mod_python import apache, util
import settings
import simplejson as json
import condition

from rtsutils.db_connection import DBConnection

def getAgreement(request):
    request.content_type = "application/json"
    
    form = util.FieldStorage(request)
    worker_id = form['workerid'].value
    
    agreed = getAgreementForWorker(worker_id)
    result = { 'read_instructions':  agreed }
    
    request.write(json.dumps(result))
    
def getAgreementForWorker(worker_id):
    db=DBConnection()
    
    result = db.query_and_return_array("""SELECT read_instructions FROM workers WHERE workerid = %s""", (worker_id, ))
    if len(result) == 0:
        # they haven't been initialized; initialize and try again
        # TODO: This is a hack...there should be a more principled way to
        # initialize the worker ID. Maybe we put that code at the top of the
        # word_clicker.mpy?
        new_condition = condition.setRandomCondition(worker_id)
        return getAgreementForWorker(worker_id)
    else:
        agreed = bool(result[0]['read_instructions'])
        return agreed
    
def setAgreement(request):
    form = util.FieldStorage(request)
    worker_id = form['workerid'].value
    
    db=DBConnection()
    
    result = db.query_and_return_array("""UPDATE workers SET read_instructions = TRUE WHERE workerid = %s""", (worker_id, ))