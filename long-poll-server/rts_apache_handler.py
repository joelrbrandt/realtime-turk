from mod_python import apache, util

import socket
import time
import thread
import simplejson

import rts_config

SEPERATOR = "\r\n\r\n"
SEPERATOR_LENGTH = len(SEPERATOR)

def handler(req):
    if req.method != "GET" and req.method != "POST":
        req.content_type='text/plain'
        return apache.HTTP_METHOD_NOT_ALLOWED  

    if req.uri.find('robots.txt') >= 0:
        req.content_type='text/plain'
        r = "User-agent: *\nDisallow: /"
        req.write(r)
        return apache.OK

    c = {}

    c['command'] = 'waitwork'
    c['useragent'] = None
    if req.headers_in.has_key('User-Agent'):
        c['useragent'] = req.headers_in['User-Agent']
    c['ip'] = req.connection.remote_ip
    
    c['method'] = req.method
    c['parameters'] = {}
    fs = util.FieldStorage(req)
    for i in fs.items():
        if (isinstance(i[1], util.StringField)):
            c['parameters'][str(i[0])] = str(i[1])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # TODO: We should do better than just using the first port in the port list
        s.connect((rts_config.server_host, rts_config.server_port_list[0]))    
        s.sendall(simplejson.dumps(c) + "\r\n\r\n")
        buf = ""
        r = str()
        while(True):
            new = s.recv(8192)
            if len(new) == 0:
                break
            buf += new
            i = buf.find(SEPERATOR)
            if i >= 0:
                r = buf[:i].strip()
                buf = buf[(i+SEPERATOR_LENGTH):]
            if len(r) > 0:
                break
        s.close()
    except Exception, e:
        s.close()
        raise e
        # return apache.HTTP_INTERNAL_SERVER_ERROR

    o = None
    try:
        o = simplejson.loads(r)
        if o.has_key("response"):
            if o['response'] == 'success':
                req.content_type = 'text/plain'
                req.write(str(o))
                return apache.OK
            elif o['response'] == 'error':
                req.content_type = 'text/plain'
                req.write(o['message'])
                return apache.OK
        raise Exception("Got a malformed response object")
    except Exception, e:
        req.content_type = 'text/plain'
        req.write("Exception received while trying to communicate with rts server: "
                  + str(type(e)) + " " + str(e) + "\n")
        req.write("Response Object: " + str(o) + "\n")
        return apache.OK
        # raise e
        # return apache.HTTP_INTERNAL_SERVER_ERROR        


