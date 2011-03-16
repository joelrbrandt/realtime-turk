import logging
                   
import threading
import simplejson

import server

class JsonCommandServer(server.AbstractServer):
    def __init__(self, command_processor, host="localhost", portlist=[12345,]):
        server.AbstractServer.__init__(self, host, portlist)
        self._command_processor = command_processor

    def start(self):
        server.AbstractServer.start(self)
        
    def handle_connection(self, conn, addr):
        logging.info("accepted connection from " + str(addr))
        t = JsonCommandConnection(conn, addr, self)
        t.start()

    def process_command(self, cmd):
        c = None # the parsed command
        r = None # the response

        # parse the string and do some error checking
        try:
            c = simplejson.loads(cmd)
        except:
            logging.info('invalid JSON object received, ignoring')


        if c != None: # got some valid JSON, let's see if it's a command
            if type(c) != dict:
                logging.info('JSON object not a dict, ignoring')

            elif not c.has_key('command'):
                logging.info('invalid command format, ignoring')
        
            else: # it's a real command! process pings here, otherwise forward to the actual command processor
                if c['command'] == 'ping':
                    r = {'response':'pong'}
                else:
                    r = self._command_processor.process(c)
        
        if r != None:
            r = simplejson.dumps(r)

        return r
        

class JsonCommandConnection(threading.Thread):
    SEPERATOR = "\r\n\r\n"
    SEPERATOR_LENGTH = len(SEPERATOR)
    
    def __init__(self, conn, addr, server):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self._conn = conn
        self._addr = addr
        self._server = server

        self._buffer = str()
        
    def run(self):
        logging.debug('connection thread started')
        try:
            while(True):
                new = self._conn.recv(8192)
                if len(new) == 0: # connection is closed
                    break
                self._buffer += new
                i = self._buffer.find(JsonCommandConnection.SEPERATOR)
                cmd = str()
                if i >= 0:
                    cmd = self._buffer[:i].strip()
                    self._buffer = self._buffer[(i+JsonCommandConnection.SEPERATOR_LENGTH):]
                if len(cmd) > 0:
                    self.process_command(cmd)
        except Exception, e:
            logging.exception('received an exception in the connection to address ' + str(self._addr) + ', closing socket:')
            self._conn.close()
        logging.debug('connection thread exiting normally')
    
    def process_command(self, cmd):
        r = self._server.process_command(cmd)
        if r != None:
            self._conn.send(r + "\r\n\r\n")
