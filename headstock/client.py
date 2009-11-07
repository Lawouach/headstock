# -*- coding: utf-8 -*-
"""
=================
XMPP client usage
=================
This modules defines the base XMPP client classes in charge of

* connecting to the XMPP server
* sending/receiving data to/from the socket stream
* registering/unregistering handlers from the XML parser

You may use any of the client class as-is or
inherit from one of them to redefine at will.

Initialize XMPP client and stream
---------------------------------
The most basic use of the client:

from headstock.client import AsyncClient
c = AsyncClient(u'user@domain', u'secret', hostname='localhost', port=5222)
c.set_log(stdout=True)
c.run()

This will not do much aside from setting
the XMPP stream up and connect initiate a
XMPP session with the server.

Note that the `run` method will block. To stop
a client you may call `stop`.

TLS can be enabled by setting the `tls`
paremeter to `True`. TLS is provided by the
`ssl` module.

The default client uses the `asyncore` module to
perform the socket handling but you may also
use a Kamaelia or Tornado based client instead.


Make your XMPP client receive stanzas
-------------------------------------
In order to make the client actually do something,
you must register an instance of a class which
defines some XMPP handler as follow:

import headstock

class Basic(object):
    @headstock.xmpphandler('item', XMPP_ROSTER_NS)
    def roster(self, e):
        self.client.log("Contact '%s' %s with subscription: %s" % (e.get_attribute_value('name', ''),
                                                                   e.get_attribute_value('jid', ''),
                                                                   e.get_attribute_value('subscription', '')))

    @headstock.xmpphandler('presence', XMPP_CLIENT_NS)
    def presence(self, e):
        self.client.log("Received '%s' presence from: %s" % (e.get_attribute_value('type', 'available'),
                                                             e.get_attribute_value('from')))

c.register(Basic())


The `xmpphandler` decorator tells the client which
stanza it expects to receive. It uses qualified name
of stanzas to do so: local name and namespace.

It also accepts two other parameters allowing to
unregister the handler once it has been called the
first time. The other one allows to forget the
matched stanza once the handler was applied. This
ensures memory won't grow out of hand.

Note that your handler may return a bridge element which
will be serialized and sent onto the wire.

To remove an instance from being used, you can call:

c.unregister(inst)


Send stanza
-----------
The `xmpphandler` decorator is a one-way track. It tells
the client where to dispatch incoming stanzas and permits to
respond to received stanza.

from headstock.lib.utils import generate_unique
from bridge.common import XMPP_CLIENT_NS

class Basic(object):
    def ready(self, client):
        self.client = client

    def message(self, jid, text):
        m = E(u"message", attributes={u'from': unicode(self.client.jid),
                                      u'to': unicode(jid), u'type': u'chat',
                                      u'id': generate_unique()},
              namespace=XMPP_CLIENT_NS)
        E(u'body', content=text, namespace=XMPP_CLIENT_NS, parent=m)
        
        self.client.send_stanza(m)

b = Basic()
b.message("somefriend@domain", u"blah blah")


The trick to make your class able to use the client
instance is to declare a `ready(client)` method which will be
called by the client once the session has been established.

Your class may then keep a reference to the client instance
provided and use the client API at will, mainly:

    * send_stanza(e)
    * send_raw_stanza(string)

The first one expects a `bridge.Element` instance whilst
the other one expects just a string to be sentd as-is on
the wire. This means you do not have to use bridge to
generate your stanzas.


Register on IQ stanzas based on their type and/or id
----------------------------------------------------
In some circumstances you may need to react to a stanza
like fhe following:
    <iq id="aab" type="result" />


One cannot register a handler using the `xmpphandler`
decorator to such stanza. Instead you can do this:

    self.client.register_on_iq(somefunc, type="result", id="aab", once=True)

This will call `somefunc(e)` when the appropriate
stanza is received. Setting the parametre `once`
ensures it will be unregistered automatically as well.


Cleanup resources when client stops
-----------------------------------
Your classes may need to perform some operations when
the client shuts down. To do so your class must declare
some methods:

    class Basic(object):
        def stopping(self):
            # Called before the socket is closed
            # unless it was closed by the server
            # already

        def cleanup(self):
            # Called after the connection was closed

        def terminated(self):
            # Called at the very end of the
            # shutdown process


Register your user
------------------
In order to register your user you just need to
set the `registerclass` parameter of the client class
to a class which subclass the `Register` class.


Use a Kamaelia client
---------------------

If you wish to use Kamaelia rather than the default
client you only need to do:

from headstock.client import KamaeliaClient
c = KamaeliaClient(u'user@domain', u'secret', hostname='localhost', port=5222)
c.set_log(stdout=True)
c.run()


Use a Tornado client
--------------------

If you wish to use Kamaelia rather than the default
client you only need to do:

from headstock.client import TornadoClient
c = TornadoClient(u'user@domain', u'secret', hostname='localhost', port=5222)
c.set_log(stdout=True)
c.run()

If you prefer that the client doesn't start the Tornado
ioloop itself, use the following instead:

c.run(start_loop=False)


"""
import asyncore
import inspect
import socket
import ssl
from functools import partial
from xml.sax import SAXParseException

from headstock.lib.jid import JID
from headstock.register import Register
from headstock.lib.logger import Logger
from headstock.error import HeadstockAuthenticationSuccess, \
     HeadstockSessionBound, HeadstockStartTLS, HeadstockStreamError
from headstock.stream import Stream

from bridge import Element as E
from bridge.parser import DispatchParser

__all__ = ['BaseClient', 'AsyncClient']

class BaseClient(object):
    def __init__(self, jid, password, tls=False, registerclass=None):
        self.parser = DispatchParser()

        self.handlers = []
        self.iq_handlers = []
        
        self.logger = None
        self.jid = JID.parse(jid)
        
        self.stream = Stream(self.jid, password, tls=tls, register=registerclass != None)
        self.register(self.stream)
        self.parser.register_default(self.default_handler)

        if registerclass:
            self.register(registerclass(self, self.jid.node, password, unicode(self.jid)))

    def set_log(self, path=None, stdout=False):
        self.logger = Logger(path=path, stdout=stdout, name=self.jid.node)

    def default_handler(self, e):
        handled = False
        if e.xml_name == u'iq':
            for stanza_id, stanza_type, handler, once in self.iq_handlers:
                if e.get_attribute_value('type') == stanza_type:
                    if e.get_attribute_value('id') == stanza_id:
                        handled = True
                        if once:
                            self.unregister_from_iq(handler, stanza_type,
                                                    stanza_id, once)
                        self.wrap_handler(e, handler, once, True)

        if not handled:
            self.log(e, 'INCOMING (DEFAULT HANDLER)')
                    
    def log(self, stanza=None, prefix='', traceback=False):
        if self.logger:
            if traceback:
                self.logger.error()
            if stanza:
                if isinstance(stanza, E):
                    stanza = stanza.xml(omit_declaration=True, indent=False)
                self.logger.log('%s %s' % (prefix, stanza))

    def send_stanza(self, stanza):
        if isinstance(stanza, E):
            stanza = stanza.xml(omit_declaration=True, indent=False)

        self.send_raw_stanza(stanza)

    def register_on_iq(self, handler, type=None, id=None, once=False):
        self.iq_handlers.append((id, type, handler, once))

    def unregister_from_iq(self, handler, type=None, id=None, once=False):
        self.iq_handlers.remove((id, type, handler, once))

    def register(self, handler):
        self.handlers.append(handler)
        members = inspect.getmembers(handler, inspect.ismethod)
        for name, member in members:
            if hasattr(member, 'handler') and member.handler is True:
                local_name = member.xmpp_local_name

                if local_name is not None:
                    if not isinstance(local_name, list):
                        local_name = [local_name]
                    
                    for name in local_name:
                        p = partial(self.wrap_handler, handler=member,
                                    fire_once=member.fire_once, forget=member.forget)
                        self.parser.register_on_element(name, p, member.xmpp_ns)
                    
    def unregister(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)
            
        members = inspect.getmembers(handler, inspect.ismethod)
        for name, member in members:
            if hasattr(member, 'handler'):
                local_name = member.xmpp_local_name

                if local_name is not None:
                    if not isinstance(local_name, list):
                        local_name = [local_name]
                        
                    for name in local_name:
                        self.parser.unregister_on_element(name, member.xmpp_ns)

    def wrap_handler(self, e, handler, fire_once, forget):
        self.log(e, 'INCOMING')
        
        if fire_once:
            self.parser.unregister_on_element(e.xml_name, e.xml_ns)

        stanza = None
        try:
            stanza = handler(e)
        except HeadstockStartTLS:
            self.start_tls()
        except HeadstockAuthenticationSuccess:
            self.parser.reset()
            self.send_stream_header()
        except HeadstockSessionBound:
            self.jid = self.stream.jid
            self.send_stanza(self.stream.notify_presence())
            self.send_stanza(self.stream.ask_roster())
            self.unregister(self.stream)
            self.ready()
        except HeadstockStreamError:
            pass
        else:
            if stanza:
                if isinstance(stanza, list):
                    map(self.send_stanza, stanza)
                else:
                    self.send_stanza(stanza)

        if forget:
            e.forget()

    ##########################################
    # Public API to be overriden if needed
    ##########################################
    def send_stream_header(self):
        header = self.stream.stream_header()
        self.send_stanza(header)
            
    def send_raw_stanza(self, stanza):
        raise NotImplemented()

    def start_tls(self):
        raise NotImplemented()

    def tls_ok(self):
        self.parser.reset()
        self.send_stream_header()

    def start(self):
        pass

    def stop(self):
        ending = self.stream.terminate()
        self.log(ending, 'OUTGOING')
        self.send_raw_stanza(ending)
            
    def socket_error(self, msg=None):
        self.log(msg or "Socket Error", 'ERROR')
    
    def ready(self):
        for handler in self.handlers:
            if hasattr(handler, 'ready'):
                handler.ready(self)

    def stopping(self):
        for handler in self.handlers:
            if hasattr(handler, 'stopping'):
                handler.stopping()

    def cleanup(self):
        self.log("Cleaning up before terminating the XMPP client")
        for handler in self.handlers:
            if hasattr(handler, 'cleanup'):
                handler.cleanup()
                
    def terminated(self):
        self.log("XMPP client terminated")
        for handler in self.handlers:
            if hasattr(handler, 'terminated'):
                handler.terminated()
        self.handlers = []


class AsyncClient(asyncore.dispatcher, BaseClient):
    def __init__(self, jid, password, hostname='localhost', port=5222, tls=False, register=False):
        asyncore.dispatcher.__init__(self)
        delattr(asyncore.dispatcher, 'log')
        
        BaseClient.__init__(self, jid, password, tls, register)
        
        self.buffer = ""

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((hostname, port))

    def send_raw_stanza(self, stanza):
        BaseClient.log(self, stanza, 'OUTGOING')
        self.buffer += stanza

    def start_tls(self):
        assert ssl, "Python 2.6+ and OpenSSL required for SSL"
        self.socket = ssl.wrap_socket(self.socket, server_side=False)
        self.tls_ok()

    def start(self):
        self.run(start_loop=False)
        
    def stop(self):
        self.stopping()
        
        if self.connected:
            BaseClient.stop(self)
            self.close()

        self.cleanup()

        self.terminated()

    def run(self, start_loop=True):
        header = self.stream.stream_header()
        self.send_raw_stanza(header)
        
        if start_loop:
            asyncore.loop(use_poll=True)
        
    def writable(self):
        return len(self.buffer) > 0

    def handle_error(self):
        BaseClient.socket_error(self)
        self.stop()
        
    def handle_close(self):
        self.stop()

    def handle_read(self):
        data = self.recv(4096)
        try:
            self.parser.feed(data)
        except SAXParseException, exc:
            self.log(traceback=True)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

try:
    from Axon.Component import component
    from Axon.Ipc import shutdownMicroprocess, producerFinished
    
    from Kamaelia.Chassis.Graphline import Graphline
    from Kamaelia.Internet.TCPClient import TCPClient
    HAS_KAMAELIA = True
except ImportError:
    HAS_KAMAELIA = False
    
if HAS_KAMAELIA:
    __all__.append("KamaeliaClient")
    
    class KamaeliaClient(component, BaseClient):
        Inboxes = {"inbox"      : "",
                   "tcp-control": "Errors bubbling up from the TCPClient component",
                   "tlssuccess" : "",
                   "control"    : "Shutdown the client stream"}

        Outboxes = {"outbox"  : "",
                    "signal"  : "Shutdown signal",
                    "starttls": ""}

        def __init__(self, jid, password, hostname='localhost', port=5222, tls=False, register=False):
            super(KamaeliaClient, self).__init__()
            BaseClient.__init__(self, jid, password, tls, register)

            self.graph = Graphline(client = self,
                                   tcp = TCPClient(hostname, port),
                                   linkages = {('client', 'outbox'): ('tcp', 'inbox'),
                                               ("tcp", "outbox") : ("client", "inbox"),
                                               ("tcp", "signal") : ("client", "tcp-control"),
                                               ("client", "starttls") : ("tcp", "makessl"),
                                               ("tcp", "sslready") : ("client", "tlssuccess")})
            self.addChildren(self.graph)
            self.link((self, 'signal'), (self.graph, 'control'))

        def send_raw_stanza(self, stanza):
            self.send(stanza, 'outbox')
        
        def start_tls(self):
            self.send('', 'starttls')

        def start(self):
            self.activate()

        def stop(self):
            BaseClient.stop(self)

        ##########################################
        # Axon specific API
        ##########################################
        def initializeComponents(self):
            self.graph.activate()
            return 1

        def main(self):
            yield self.initializeComponents()
            yield 1

            self.send_stream_header()

            self.running = True
            while self.running:
                if self.dataReady("tcp-control"):
                    mes = self.recv("tcp-control")
                    if isinstance(mes, shutdownMicroprocess) or \
                            isinstance(mes, producerFinished):
                        self.stopping()            
                        self.log(mes.message, prefix='ERROR')
                        self.socket_error(mes.message)
                        self.send(shutdownMicroprocess(), "signal")
                        yield 1
                        self.running = False

                if self.dataReady("control"):
                    mes = self.recv("control")
                    if isinstance(mes, shutdownMicroprocess) or \
                           isinstance(mes, producerFinished):
                        self.stopping()            
                        self.send(shutdownMicroprocess(), "signal")
                        yield 1
                        self.running = False

                if self.dataReady("tlssuccess"):
                    self.recv("tlssuccess")
                    yield 1
                    self.tls_ok()
                    yield 1
                
                if self.dataReady("inbox"):
                    data = self.recv('inbox')
                    try:
                        self.parser.feed(data)
                    except SAXParseException, exc:
                        self.log(traceback=True)

                if self.running and not self.anyReady():
                    self.pause()

                yield 1

            self.cleanup()

            self.send(shutdownMicroprocess(), "signal")

            yield 1

            self.graph.removeChild(self)

            while not self.graph.childrenDone():
                if not self.anyReady():
                    self.graph.pause()

                yield 1

            while not self.childrenDone():
                if not self.anyReady():
                    self.pause()

                yield 1

            self.graph = None

            self.terminated()

        def childrenDone(self):
            for child in self.childComponents():
                if child._isStopped():
                    self.removeChild(child)

            return 0 == len(self.childComponents())

try:
    import socket
    import errno
    import logging
    from tornado.iostream import IOStream
    from tornado import ioloop
    HAS_TORNADO = True
    try:
        import ssl # Python 2.6+
    except ImportError:
        ssl = None
except ImportError:
    HAS_TORNADO = False
    
if HAS_TORNADO:
    class _IOStream(IOStream):
        def _handle_read(self):
            try:
                chunk = self.socket.recv(self.read_chunk_size)
            except socket.error, e:
                if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                else:
                    logging.warning("Read error on %d: %s",
                                    self.socket.fileno(), e)
                    self.close()
                    return
            if not chunk:
                self.close()
                return
            self._read_buffer += chunk
            callback = self._read_callback
            self._read_callback = None
            self._read_bytes = None
            callback(self._consume(len(self._read_buffer)))

    class TornadoClient(BaseClient):
        def __init__(self, jid, password, hostname='localhost', port=5222, tls=False, register=False):
            BaseClient.__init__(self, jid, password, tls, register)
            
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            s.connect((hostname, port))
            self.io = _IOStream(s)
            self.io.set_close_callback(self.socket_error)
            self._read()

        def socket_error(self):
            BaseClient.socket_error(self)
            self.stop()

        def send_raw_stanza(self, stanza):
            self.log(stanza, 'OUTGOING')
            self.io.write(stanza)

        def start_tls(self):
            assert ssl, "Python 2.6+ and OpenSSL required for SSL"
            self.io.io_loop.remove_handler(self.io.socket.fileno())
            self.io.socket = ssl.wrap_socket(self.io.socket, server_side=False)
            self.io.io_loop.add_handler(self.io.socket.fileno(),
                                        self.io._handle_events, self.io._state)
            self.tls_ok()

        def start(self):
            self.run(start_loop=False)
            
        def stop(self, stop_loop=False):
            self.stopping()
            
            if not self.io.closed():
                BaseClient.stop(self)
                
                self.io._close_callback = None
                self.io.close()

            self.cleanup()

            if stop_loop:
                ioloop.IOLoop.instance().stop()

            self.terminated()

        def run(self, start_loop=True):
            header = self.stream.stream_header()
            self.send_raw_stanza(header)
            
            if start_loop:
                ioloop.IOLoop.instance().start()
                  
        def handle_read(self, data):
            try:
                self.parser.feed(data)
            except SAXParseException, exc:
                self.log(traceback=True)
            self._read()
      
        def _read(self):
            self.io.read_bytes(4096, self.handle_read)
