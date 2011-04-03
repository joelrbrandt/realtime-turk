from mod_python import apache

""" Handler for /video/ requests only"""

def handler(request):
    uri_parts = request.uri.split("/")
    while '' in uri_parts:
        uri_parts.remove('')

    if uri_parts[-1] == "ready":
        import ready
        ready.is_ready(request)
        return apache.OK
        
    elif uri_parts[-1] == "location":
        import location_ping
        location_ping.locationPing(request)
        return apache.OK

    elif uri_parts[-1] == "random":
        import random
        random.getRandomVideo(request)
        return apache.OK

    elif uri_parts[-1] == "log":
        import log
        log.log(request)
        return apache.OK

    elif uri_parts[-1] == "submit":
        import submit
        submit.record_and_redirect(request)
        return apache.OK

    else:
        # request.content_type = "text/plain"
        # request.write("Error: can't find a command with the name " + str(uri_parts) + "\n")
        return apache.HTTP_NOT_IMPLEMENTED
