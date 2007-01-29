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

    def _connect(self):
        s = None
        for res in socket.getaddrinfo(self.host, self.port, socket.AF_UNSPEC,
                                      socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
                #s.settimeout(1.0)
            except socket.error, (err, strerror):
                if err == errno.EINPROGRESS:
                    break
                continue

        s.connect((self.host, self.port))
        self.sock = s

    def connect(self):
        self._connect()

    def _disconnect(self):
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

        data = []
        try:
            incoming = r(size)
            data.append(incoming)
        except:
            pass
        while select.select([self.sock], [], [], 0.1)[0]:
            try:
                incoming = r(size)
            except:
                incoming = None
            if not incoming: break
            data.append(incoming)
        return ''.join(data)

    def communicate(self, data, size=4096):
        self._send(data)
        data = self._recv(size)
        return data

if __name__ == '__main__':
    from bridge.parser.bridge_amara import Parser
    from bridge import Element as E
    E.parser = Parser

    import headstock

    class H(object):    
        def handle_connected(self, response):
            pass
        handle_connected.headstock = 'connected'

        def handle_item_not_found(self, response):
            print response
        handle_connected.headstock = 'item-not-found'


    from headstock.lib.registry import Registry
    #r = H()
    r = Registry()
    
    from headstock.core.stream import Stream
    from headstock.core.message import Message
    from headstock.extension.discovery import Disco
    from headstock.extension.pubsub import Service

    c = Client('localhost', 5222)
    s = Stream(u'localhost', c, u'headstock')
    v = Service(s)
    d = Disco(s)

    s.set_registry(r)
    s.set_auth('test', 'test')
    jid = s.initiate()
    d.set_jids(unicode(jid), u'pubsub.localhost')
    #d.ask_features(u'pubsub.localhost')
    #d.set_jids(unicode(jid), u'conference.localhost')
    #d.ask_features(u'conference.localhost')
    #d.ask_nodes()
    #d.ask_identities(u'/muse')
    #n.create(jid, u'pubsub.localhost', u'test')
    v.set_jids(unicode(jid), u'pubsub.localhost')
    v.create_node(u'muse')
    e = v.subscribe(u'/muse')
    t = E(u't')
    v.publish(u'/muse', t)
    #e = v.subscribe(u'/test')
    #v.purge(u'/muse')
    #v.delete(u'/test/1eMqAWd0IMLBJWf8TyNG885v427D5cNq40f6bzyb')
    v.unsubscribe(u'/muse', e[0].pubsub.subscription[0].subid)
    #s.propagate(Message(body=u'hi there', from_jid=jid, to_jid=u'test2@localhost'))
    s.terminate()
