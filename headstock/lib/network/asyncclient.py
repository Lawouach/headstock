#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tlslite.api import *

__all__ = ['AsyncClient']

##########################################################
# Async client
##########################################################
import socket
import asyncore

class AsyncClient(asyncore.dispatcher):
    def __init__(self, host, port, certificate=None,
                 certificate_key=None, certificate_password_cb=None):
        asyncore.dispatcher.__init__(self)
        self.host = host
        self.port = port
        self._parser = None
        self.buffer = []

        self.certificate = certificate 
        self.certificate_key = certificate_key
        self.certificate_password_cb = certificate_password_cb

    def connect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = self.socket
        asyncore.dispatcher.connect(self, (self.host, self.port))

    def start_tls(self):
        x509 = X509()
        x509.parse(self.certificate)
        certChain = X509CertChain([x509])
        privateKey = parsePEMKey(self.certificate_key, private=True,
                                 passwordCallback=self.certificate_password_cb)
        
        connection = TLSConnection(self.socket)
        connection.handshakeClientCert(certChain, privateKey)
        self.conn = connection
                                 
    def set_parser(self, parser):
        self._parser = parser

    def get_parser(self):
        return self._parser

    def handle_connect(self):
        pass

    def handle_close(self):
        try:
            self._parser.close()
        except:
            pass
        self._parser = self._handler = None
        self.conn.close()
        self.close()

    def recv(self, buffer_size):
        try:
            data = self.conn.recv(buffer_size)
            if not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                self.handle_close()
                return ''
            else:
                return data
        except socket.error, why:
            # winsock sometimes throws ENOTCONN
            if why[0] in [ECONNRESET, ENOTCONN, ESHUTDOWN]:
                self.handle_close()
                return ''
            else:
                raise

    def handle_read(self):
        data = self.recv(4096)
        #print data
        if self._parser and data:
            self._parser.feed(data)

    def writable(self):
        return (len(self.buffer) > 0)
    
    def propagate(self, data):
        self.buffer.append(data)

    def send(self, data):
        try:
            result = self.conn.send(data)
            return result
        except socket.error, why:
            if why[0] == EWOULDBLOCK:
                return 0
            else:
                raise
            return 0

    def handle_write(self):
        #print self.buffer
        sent = self.send(''.join(self.buffer))
        self.buffer = self.buffer[sent:]

