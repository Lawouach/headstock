#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Kamaelia.Internet.TCPClient import TCPClient
from Axon.ThreadedComponent import threadedcomponent

__all__ = ['ThreadedClient']


class ThreadedClient(threadedcomponent):
    def __init__(self, host, port, certificate=None,
                 certificate_key=None, certificate_password_cb=None):
        super(ThreadedClient, self).__init__()
        
        self.connected = False
        self.host = host
        self.port = port
        self.client = TCPClient(self.host, self.port, delay=1)
        self.addChildren(self.client)
        self.link((self.client, "outbox"), (self, "inbox")) 
        self.link((self, "outbox"), (self.client, "inbox")) 
        self._parser = None
        self.incoming_cb = None
        self.keep_running = True
        self.certificate = certificate 
        self.certificate_key = certificate_key
        self.certificate_password_cb = certificate_password_cb
      
    def set_parser(self, parser):
        self._parser = parser

    def get_parser(self):
        return self._parser

    def start_tls(self):
        raise NotImplemented
       
    def propagate(self, data, size=4096):
        print "-> ", data
        self.send(data, "outbox")

    def stop(self):
        self.keep_running = False

    def main(self):
        while self.keep_running:
            if self.dataReady("inbox"):
                data = self.recv("inbox")
                print "<- ", data
                self._parser.feed(data)
        
