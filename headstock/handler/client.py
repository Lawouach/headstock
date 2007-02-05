#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import select
import errno

from asyncore import dispatcher

##########################################################
# Async client
##########################################################
class AsyncClient(dispatcher):
    def __init__(self, host, port):
        dispatcher.__init__(self)
        self.host = host
        self.port = port
        self._parser = None
        self._handler = None
        self.buffer = []

    def connect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        dispatcher.connect(self, (self.host, self.port))

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
        self.close()

    def handle_read(self):
        data = self.recv(4096)
        print data
        if self._parser and data:
            self._parser.feed(data)

    def writable(self):
        return (len(self.buffer) > 0)
    
    def propagate(self, data):
        self.buffer.append(data)

    def handle_write(self):
        sent = self.send(''.join(self.buffer))
        self.buffer = self.buffer[sent:]
        
##########################################################
# Sync client
##########################################################
class Client(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.run = True
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

    def _connect(self):
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
        self.sock = s

    def connect(self):
        self._connect()

    def _disconnect(self):
        self.run = False
        try:
            self._parser.close()
        except:
            pass
        self._parser = self._handler = None
        if self.sock:
            self.sock.close()

    def disconnect(self):
        self._disconnect()
    
    def _send(self, data):
        if isinstance(data, unicode):
            data = data.encode('utf-8')

        print "####################"
        print data
        if hasattr(self.sock, 'write'):
            self.sock.write(data)
        else:
            self.sock.sendall(data)

    def _recv(self, size=4096):
        if hasattr(self.sock, 'read'):
            r = self.sock.read
        else:
            r = self.sock.recv
        try:
            data = r(size)
        except:
            pass
        print data
        if self._parser and data:
            self._parser.feed(data)
        return data

    def propagate(self, data, size=4096):
        self._send(data)
    
    def loop(self, timeout=0):
        while self.run:
            self.process(timeout)
            
    def process(self, timeout=0):
        can_read = select.select([self.sock], [], [], timeout)[0]
        if can_read:
            try:
                self._recv()
            except:
                pass
