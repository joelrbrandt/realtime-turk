from mod_python import apache, util
import servertime

def handler(request):
    servertime.servertime(request)
    return apache.OK
