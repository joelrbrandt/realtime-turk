from mod_python import apache

def handler(request):
    uri_parts = request.uri.split("/")
    while '' in uri_parts:
        uri_parts.remove('')

    if uri_parts[-1] == "time":
        import servertime
        servertime.servertime(request)
        return apache.OK
        
    elif uri_parts[-1] == "condition":
        import condition
        condition.loadCondition(request)
        return apache.OK 

    elif uri_parts[-1] == "testtimer":
        import testtimer
        testtimer.testTimer(request)
        return apache.OK
        
    elif uri_parts[-1] == "gettext":
        import gettext
        gettext.getText(request)
        return apache.OK
        
    elif uri_parts[-1] == "log":
        import logging
        logging.log(request)
        return apache.OK
        
    elif uri_parts[-1] == "bonus":
        import bonus
        bonus.grantBonus(request)
        return apache.OK
        
    elif uri_parts[-2] == "agreement":
        import agreement    
        if uri_parts[-1] == "get":
            agreement.getAgreement(request)
            return apache.OK
        elif uri_parts[-1] == "set":
            agreement.setAgreement(request)
            return apache.OK
            
    elif uri_parts[-1] == "verify":
        import verify
        verify.verify(request)
        return apache.OK
        
    else:
        # request.content_type = "text/plain"
        # request.write("Error: can't find a command with the name " + str(uri_parts) + "\n")
        return apache.HTTP_NOT_IMPLEMENTED
        
