import socket
import thread
import threading
import logging

class AbstractServer:
    DEFAULT_TIMEOUT = 5 #seconds
    
    def __init__(self, host="localhost", portlist=[12346,]):
        self.is_connected = False
        self.host = host
        self.portlist = portlist
        self.sock = None
        self.port = None
        self.accept_cv = threading.Condition()
        self.do_accepting = False
        
    def stop(self):
        if (self.sock != None):
            logging.debug('closing socket...')
            self.do_accepting = False
            self.accept_cv.acquire()    
            self.sock.close()
            self.sock = None
            self.port = None
            self.accept_cv.notifyAll()
            self.accept_cv.release()
            logging.debug('...closed')
            
    def start(self):
        logging.debug('starting server...')
        self.stop()
        self.accept_cv.acquire()
        for p in self.portlist:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(AbstractServer.DEFAULT_TIMEOUT)
                self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.sock.bind((self.host, p))
                self.sock.listen(5)
                self.port = p
                logging.debug('...started on port ' + str(self.port))
                break
            except Exception, e: # port was in use
                logging.debug('...got Exception: ' +  str(e))
                self.sock = None
                logging.debug('...port ' + str(p) + ' already in use, trying next...')
        if self.sock != None:
            logging.debug('starting accepting thread...')
            self.do_accepting = True
            thread.start_new_thread(self.accept_connections, ())
            logging.debug('...accepting thread started')
            self.accept_cv.notifyAll()
        else:
            logging.debug('...FAILED to start server (all ports in use?)')

        self.accept_cv.release()
        
    def accept_connections(self):
        while (self.do_accepting):
            self.accept_cv.acquire()
            if self.sock == None:
                self.accept_cv.wait(AbstractServer.DEFAULT_TIMEOUT)
            sock = self.sock
            if sock != None:
                try:
                    conn, addr = self.sock.accept()
                    self.handle_connection(conn, addr)
                except: # timeout or we don't actually have a socket. Regardless, someone else's problem
                    pass
            self.accept_cv.release()

    def handle_connection(self, conn, addr):
        logging.info("accepted connection from " + str(addr))
        conn.send("abstract server doesn't implement anything for connections!\n")
        conn.close()
