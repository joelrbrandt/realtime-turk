import logging

import sys
import time

import rts_config
import work_coordinator
import json_command_server

from optparse import OptionParser

def start_new_rts():
    w = work_coordinator.WorkCoordinator()
    s = json_command_server.JsonCommandServer(w,
                                              host=rts_config.server_host,
                                              portlist=rts_config.server_port_list)
    s.start()
    return (w,s)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-l", "--log", dest="logfile", help="log to FILE", metavar="FILE")
    (options, args) = parser.parse_args()
    if options.logfile:
        logging.basicConfig(level=logging.DEBUG,
                            format='[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s',
                            filename=options.logfile,
                            filemode='w')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='[%(asctime)s] %(levelname)s (%(filename)s:%(lineno)d) %(message)s',
                            stream=sys.stdout)
    start_new_rts()
    
    while True:
        time.sleep(1000)
