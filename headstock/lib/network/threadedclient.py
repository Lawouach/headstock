#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['ThreadedClient']

##########################################################
# Threaded client
##########################################################
import sys
import socket
import time
import thread
import threading
import select
import Queue
import errno

class ThreadedClient(threading.Thread):
    def __init__(self, host, port, certificate=None,
                 certificate_key=None, certificate_password_cb=None):
        threading.Thread.__init__(self)
        self.connected = False
        self.host = host
        self.port = port
        self.lock = threading.Lock()
        self.sock = self.conn = None
        self.keep_running = True
        self._parser = None
        self.incoming = Queue.Queue(0)
        self.incoming_cb = None
        self.certificate = certificate 
        self.certificate_key = certificate_key
        self.certificate_password_cb = certificate_password_cb
        
    def set_parser(self, parser):
        self._parser = parser

    def get_parser(self):
        return self._parser

    def start_tls(self):
        from tlslite.api import X509, X509CertChain, parsePEMKey, TLSConnection

        try:
            self.lock.acquire()
            x509 = X509()
            x509.parse(self.certificate)
            certChain = X509CertChain([x509])
            privateKey = parsePEMKey(self.certificate_key, private=True,
                                     passwordCallback=self.certificate_password_cb)

            connection = TLSConnection(self.sock)
            setattr(connection, 'fileno', connection.sock.fileno)
            connection.handshakeClientCert(certChain, privateKey)
            self.conn = connection
        finally:
            self.lock.release()
        
    def connect(self):
        s = None
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC,
                                      socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
                s.settimeout(1.0)
            except socket.error, (err, strerror):
                if err == errno.EINPROGRESS:
                    break
                continue

        s.connect((self.host, self.port))
        self.lock.acquire()
        self.sock = self.conn = s
        self.connected = True
        self.lock.release()

    def disconnect(self):
        self.keep_running = False
        try: self.conn.close()
        except: pass
        try: self.sock.close()
        except: pass
        try: self._parser.close()
        except: pass
        self._parser = self._handler = None
        self.connected = False
        
    def propagate(self, data, size=4096):
        #print "-> ", data
        self.conn.send(data)
    
    def run(self):
        while self.keep_running:
            fds = data = None
            try:
                time.sleep(0.002)
                self.lock.acquire()
                conn = self.conn
                fds = select.select([conn], [], [], 0.05)[0]
                if fds:
                    data = fds[0].recv(4096)
            finally:
                self.lock.release()

            if data:
                #print "<- ", data
                if self.incoming:
                    self.incoming.put(data)
                if self.incoming_cb:
                    self.incoming_cb(data)

