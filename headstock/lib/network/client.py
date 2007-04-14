#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import asyncore

from tlslite.api import *

__all__ = ['ThreadedClient', 'AsyncClient']

##########################################################
# Async client
##########################################################
class AsyncClient(asyncore.dispatcher):
    def __init__(self, host, port, certificate=None,
                 certificate_key=None, certificate_password_cb=None):
        asyncore.dispatcher.__init__(self)
        self.host = host
        self.port = port
        self._parser = None
        self._handler = None
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

    def set_handler(self, handler):
        self._handler = handler

    def get_parser(self):
        return self._parser

    def get_handler(self):
        return self._handler
    
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
        print data
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
        print self.buffer
        sent = self.send(''.join(self.buffer))
        self.buffer = self.buffer[sent:]


##########################################################
# Threaded client
##########################################################
import thread
import threading
import select
import errno

class ThreadedClient(threading.Thread):
    def __init__(self, host, port, certificate=None,
                 certificate_key=None, certificate_password_cb=None):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.lock = threading.RLock()
        self.sock = self.conn = None
        self.keep_running = True
        self._parser = None
        self._handler = None
        
    def set_parser(self, parser):
        self._parser = parser

    def get_parser(self):
        return self._parser

    def set_handler(self, handler):
        self._handler = handler

    def get_handler(self):
        return self._handler

    def start_tls(self):
        x509 = X509()
        x509.parse(self.certificate)
        certChain = X509CertChain([x509])
        privateKey = parsePEMKey(self.certificate_key, private=True,
                                 passwordCallback=self.certificate_password_cb)
        
        connection = TLSConnection(self.sock)
        connection.handshakeClientCert(certChain, privateKey)
        self.lock.acquire()
        self.conn = connection
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
        
    def propagate(self, data, size=4096):
        print data
        self.conn.send(data)
    
    def run(self):
        while self.keep_running:
            self.lock.acquire()
            conn = self.conn
            self.lock.release()

            fds = select.select([conn], [], [], 0.1)[0]
            
            if fds:
                data = None
                try:
                    data = fds[0].recv(4096)
                except:
                    pass
                if self._parser and data:
                    self._parser.feed(data)
                    print data
            
