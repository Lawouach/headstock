#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import select
import errno

from asyncore import dispatcher
from asynchat import async_chat

class ConnectionHandler(async_chat):
    def __init__(self, sock, addr, stream):
        async_chat.__init__(self, sock)
        self.set_terminator('')
        self.stream = stream
        self.data = [_ for _ in self.stream.initiate()]
        self.push(self.data.pop(0))
        
    def collect_incoming_data(self, data):
        print data

    def found_terminator(self):
        print "found"
        if self.data:
            next = self.data.pop(0)
            print next
            self.push(next)
            
class Service(dispatcher):
    def __init__(self, host, port, timeout=None):
        dispatcher.__init__(self) 
        self.host = host
        self.port = port
        self.timeout = timeout
        
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((self.host, self.port))
        self.listen(5)

    def handle_accept (self):
        sock, addr = self.accept()
        ConnectionHandler(sock, addr)

    def handle_close(self):
        self.close()


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
        
if __name__ == '__main__':
    from bridge.parser.bridge_expat import Parser
    from bridge import Element as E
    E.parser = Parser
    from bridge.parser.incremental import create_parser

    def user_online(p, e):
        print unicode(e.get_attribute('from'))
    
    def user_unavailable(p, e):
        print unicode(e.get_attribute('from'))

    def user_subscription_requested(p, e):
        jid = unicode(element.get_attribute('from'))
        p.allow_subscription(jid)
    
    import headstock

    from headstock.lib.registry import Registry
    from headstock.core.stream import Stream
    from headstock.core.message import Message
    from headstock.core.presence import Presence
    from headstock.core.roster import Roster
    from headstock.extension.discovery import Disco
    from headstock.extension.pubsub import Service
    
    r = Registry()
    c = Client('localhost', 5222)
    s = Stream(u'localhost', c, u'headstock')
    v = Service(s)
    d = Disco(s)

    parser, handler, output = create_parser()
    c.set_parser(parser)
    c.set_handler(handler)
    c.connect()

    p = Presence(s)
    p.register_online(user_online)
    p.register_unavailable(user_unavailable)
    p.register_subscribe(user_subscription_requested)
    
    roster = Roster(s)
    
    s.set_registry(r)
    s.set_auth('test', 'test')

    import threading
    th = threading.Thread(target=c.loop)
        
    th.start()
    s.initiate()

    import time

    while 1:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            c.run = False
            th.join()
            c.disconnect()
            break
