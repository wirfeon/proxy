#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import zmq
import struct
import binascii

PORT = int(os.environ.get('PORT', '8443'))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

def send_to_frontend(frontend, identity, message = b""):
    logger.info("SEND %s '%d'" % (binascii.hexlify(identity), len(message)))
    
    frontend.send(identity, zmq.SNDMORE)
    frontend.send(message)

def send_down(down, identity, message = b""):
    logger.info("SEND %s '%d'" % (binascii.hexlify(identity), len(message)))
    
    down.send(identity, zmq.SNDMORE)
    down.send(message)

def read_frontend(frontend, down):
    identity = frontend.recv()
    message = frontend.recv()

    logger.info("RECV %s '%d'" % (binascii.hexlify(identity), len(message)))

    send_down(down, identity, message)

def read_down(frontend, down):

    identity = down.recv()
    message = down.recv()

    logger.info("RECV %s '%d'" % (binascii.hexlify(identity), len(message)))

    send_to_frontend(frontend, identity, message)

def main():
    ctx = zmq.Context()

    addr = "tcp://0.0.0.0:%d" % PORT
    logger.info("Frontend bind to '%s'" % addr)
    frontend = ctx.socket(zmq.STREAM)
    frontend.bind(addr)
    
    down = ctx.socket(zmq.DEALER)
    down.bind("tcp://0.0.0.0:8444")
    
    poller = zmq.Poller()
    poller.register(frontend, flags = zmq.POLLIN)
    poller.register(down, flags = zmq.POLLIN)

    while 1:
        socks = dict(poller.poll())
        
        if ((frontend in socks) and (socks[frontend] == zmq.POLLIN)):
            read_frontend(frontend, down)
        if ((down in socks) and (socks[down] == zmq.POLLIN)):
            read_down(frontend, down)

    frontend.close()
    down.close()

if __name__ == '__main__':
    main()
