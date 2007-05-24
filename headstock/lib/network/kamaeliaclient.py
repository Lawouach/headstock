#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Kamaelia.Internet.TCPClient import TCPClient
from Axon.ThreadedComponent import threadedcomponent
from Kamaelia.IPC import newReader, newWriter

__all__ = ['KamaeliaClient']


class KamaeliaClient(threadedcomponent):
    Inboxes = { "inbox" : "Default inbox",
                "fromTCPClient" : "Data received from the TCP client",
                "control" : "NOT USED", }
    
    Outboxes = { "outbox" : "Default outbox",
                 "signal" : "NOT USED",
                 "toTCPClient" : "Data to be sent by the TCP client",}

    def __init__(self, host, port, certificate=None,
                 certificate_key=None, certificate_password_cb=None):
        super(KamaeliaClient, self).__init__()
        
        self.connected = False
        self.host = host
        self.port = port
        self._parser = None
        self.client = None
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
        from tlslite.api import X509, X509CertChain, parsePEMKey, TLSConnection

        x509 = X509()
        x509.parse(self.certificate)
        certChain = X509CertChain([x509])
        privateKey = parsePEMKey(self.certificate_key, private=True,
                                 passwordCallback=self.certificate_password_cb)
        
        connection = TLSConnection(self.client.sock)
        setattr(connection, 'fileno', connection.sock.fileno)
        connection.handshakeClientCert(certChain, privateKey)
        self.client.CSA.socket = connection
##         self.client.postoffice.unlinkAll()
##         for ct in self.client.setupCSA(connection):
##             ct.activate()
##         self._dolink()
        #self.client.sock = connection
        
    def connect(self):
        self.client = TCPClient(self.host, self.port)
        self._dolink()
        self.client.activate()

    def _dolink(self):
        l = self.link((self.client, "outbox"), (self, "fromTCPClient"))
        l.setShowTransit(True, "TCPoutbox")
        self.link((self, "toTCPClient"), (self.client, "inbox")) 
    
    def propagate(self, data, size=4096):
        print "-> ", data
        self.send(data, "toTCPClient")

    def disconnect(self):
        self.connected = False
        self.keep_running = False
        try:
            self._parser.close()
        except:
            pass

    def main(self):
        while self.keep_running:
            if self.dataReady("fromTCPClient"):
                data = self.recv("fromTCPClient")
                print "<- ", data
                self._parser.feed(data)
        
            if not self.client.anyReady():
                self.pause()
