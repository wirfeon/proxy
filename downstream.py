#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import zmq
import struct
import binascii

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

router_back = {}
router_up = {}

def send_up(up, identity, message = b""):
    logger.info("SEND up %s '%d'" % (binascii.hexlify(identity), len(message)))

    up.send(identity, zmq.SNDMORE)
    up.send(message)

def send_to_backend(backend, identity, message = b""):
    logger.info("SEND backend %s '%d'" % (binascii.hexlify(identity), len(message)))

    backend.send(identity, zmq.SNDMORE)
    backend.send(message)

def read_up(up, backend):
    global router_up, router_back

    identity = up.recv()
    message = up.recv()

    logger.info("RECV up %s '%d'" % (binascii.hexlify(identity), len(message)))

    if ((identity not in router_back) and (len(message) == 0)):
        logger.info("Connecting to backend")
        backend.connect("tcp://localhost:8445")

        bid = backend.recv()
        message = backend.recv()
    
        logger.info("RECV backend %s '%d'" % (binascii.hexlify(bid), len(message)))
        
        router_back[identity] = bid
        router_up[bid] = identity

        logger.info("%s %s" % (router_back, router_up))
    elif ((identity in router_back) and (len(message) == 0)):
        logger.info("Disconnecting backend")
        send_to_backend(backend, router_back[identity])
        del router_up[router_back[identity]]
        del router_back[identity]
    elif ((identity in router_back) and (len(message) > 0)):
        logger.info("Forwarding to backend")
        send_to_backend(backend, router_back[identity], message)
    else:
        logger.info("Unknown client")
        send_up(up, identity)

def read_backend(up, backend):
    global router_up, router_back

    identity = backend.recv()
    message = backend.recv()

    logger.info("RECV backend %s '%d'" % (binascii.hexlify(identity), len(message)))

    if ((identity in router_up) and (len(message) == 0)):
        logger.info("Backend closed connection")
        send_up(up, identity)
        del router_back[router_up[identity]]
        del router_up[identity]
    elif (identity not in router_up):
        logger.info("Unknown backend")
        send_to_backend(backend, identity)
    elif ((identity in router_up) and (len(message) != 0)):
        logger.info("Forwarding to client")
        send_up(up, router_up[identity], message)

def main():
    ctx = zmq.Context()

    backend = ctx.socket(zmq.STREAM)
    
    up = ctx.socket(zmq.DEALER)
    up.connect("tcp://127.0.0.1:8444")
    
    poller = zmq.Poller()
    poller.register(up, flags = zmq.POLLIN)
    poller.register(backend, flags = zmq.POLLIN)

    while 1:
        socks = dict(poller.poll())
        
        if ((up in socks) and (socks[up] == zmq.POLLIN)):
            read_up(up, backend)
        if ((backend in socks) and (socks[backend] == zmq.POLLIN)):
            read_backend(up, backend)

    up.close()
    backend.close()

if __name__ == '__main__':
    main()
