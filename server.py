#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import zmq
import binascii

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

def read_frontend(frontend):
    identity = frontend.recv()
    message = frontend.recv()

    if (len(message) == 0):
        return

    logger.info("RECV %s '%d'" % (binascii.hexlify(identity), len(message)))
    logger.info("SEND %s", binascii.hexlify(identity))

    frontend.send(identity, zmq.SNDMORE)
    frontend.send_string("HTTP/1.1 200 OK\r\n\r\n\r\n")

def main():
    ctx = zmq.Context()

    frontend = ctx.socket(zmq.STREAM)
    frontend.bind("tcp://127.0.0.1:8445")
    
    poller = zmq.Poller()
    poller.register(frontend, flags = zmq.POLLIN)

    while 1:
        socks = dict(poller.poll())
        
        if (socks[frontend] == zmq.POLLIN):
            read_frontend(frontend)

    frontend.close()

if __name__ == '__main__':
    main()
