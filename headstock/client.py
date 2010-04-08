# -*- coding: utf-8 -*-
import asyncore
import inspect
import socket
try:
    import ssl
except ImportError:
    ssl = None
from functools import partial
from xml.sax import SAXParseException

from headstock.lib.jid import JID
from headstock.register import Register
from headstock.lib.logger import Logger
from headstock.error import HeadstockAuthenticationSuccess, \
     HeadstockSessionBound, HeadstockStartTLS,\
     HeadstockStreamError, HeadstockAvailable
from headstock.stream import Stream

from bridge import Element as E
from bridge.parser import DispatchParser

__all__ = ['BaseClient', 'AsyncClient']

class BaseClient(object):
    """
    Defines a high level API by which your application connects to
    a XMPP server, creates a XMPP stream and sets the XML
    parser that will dispatch incoming stanzas to XMP handlers.

    You would not create an instance of this directly but
    use one of its subclass.

    ``jid`` Jabber identifier of the client account. It must at least be
    a bare jid.

    ``password`` Account's password.

    ``tls`` False - Flag indicating if the client should use TLS should
    the server support it.

    ``registerclass`` None - Class that will handle the registration process.
    It should be a subclass of :class:`headstock.register.Register`. The default,
    `None` means the registration process is not handled by the client.
    """
    def __init__(self, jid, password, tls=False, registerclass=None):
        self.parser = DispatchParser()

        self.running = False

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
        """
        Sets the client's logger. Note that the logger's name is
        suffixed by the jid's node so that you can create several of them
        within one single process.

        ``path`` None - Filesystem path to use a file handler for the logger.

        ``stdout`` False - Flag indicating if the logger should output to
        the standard outpout.
        """
        self.logger = Logger(path=path, stdout=stdout, name=self.jid.node)

    def default_handler(self, e):
        handled = False
        if e.xml_name == u'iq':
            for stanza_id, stanza_type, handler, once in self.iq_handlers:
                if stanza_type and e.get_attribute_value('type') != stanza_type:
                    continue
                if stanza_id and e.get_attribute_value('id') != stanza_id:
                    continue

                handled = True
                if once:
                    self.unregister_from_iq(handler, stanza_type,
                                            stanza_id, once)
                    self.wrap_handler(e, handler, once, True)

        if not handled:
            self.log(e, 'INCOMING (DEFAULT HANDLER)')
                    
    def log(self, stanza=None, prefix='', traceback=False):
        """
        Logs a stanza into its XML serialized form.

        ``stanza`` :class:`bridge.Element` instance to be serialized to a XML string.

        ``prefix`` A string to prefix the line that will be created by the logger.

        ``traceback`` False - Flag indicating the current traceback should be
        logged.
        """
        if self.logger:
            if traceback:
                self.logger.error()
            if stanza:
                if isinstance(stanza, E):
                    stanza = stanza.xml(omit_declaration=True, indent=False)
                self.logger.log('%s %s' % (prefix, stanza))

    def send_stream_header(self):
        """
        Sends the initial stream header to the server.
        """
        header = self.stream.stream_header()
        self.send_stanza(header)
            
    def send_stanza(self, stanza):
        """
        Sends a stanza onto the wire by serializing it first to XML.

        ``stanza`` :class:`bridge.Element` instance to be sent.
        """
        if isinstance(stanza, E):
            stanza = stanza.xml(omit_declaration=True, indent=False)

        self.send_raw_stanza(stanza)

    def register_on_iq(self, handler, type=None, id=None, once=False):
        """
        Registers a callable as a recipient of a Iq stanza with the
        provided `type` and/or `id` attributes.

        ``handler`` callable that must accept one single argument,
        a :class:`bridge.Element` instance.

        ``type`` None - stanza type to be matched

        ``id`` None - stanza identifier to be matched

        ``once`` False - Flag indicating if the handler should be
        unregistered automatically or not once it has been applied.
        """
        self.iq_handlers.append((id, type, handler, once))

    def unregister_from_iq(self, handler, type=None, id=None, once=False):
        """
        Unregisters a previously registered callable for a Iq stanza.

        ``handler`` callable that must accept one single argument,
        a :class:`bridge.Element` instance.

        ``type`` stanza type to be matched

        ``id`` stanza identifier to be matched

        ``once`` False - Flag indicating if the handler should be
        unregistered automatically or not once it has been applied.
        """
        self.iq_handlers.remove((id, type, handler, once))

    def register(self, handler):
        """
        Registers recipients for stanzas by going through the
        members of the provided `handler` instance. To be taken into
        account those members must have an attribute called `handler`
        set to `True` as well as a `xmpp_local_name` indicating
        which element is expected.

        The actual methods will be wrapped into ``headstock.client.BaseClient.wrap_handler``
        which will call the method and traps some of the ``headstock.error`` exceptions
        and act accordingly.
        
        ``handler`` instance of an object that defines at least
        one method with the expected properties.
        """
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
        """
        Unregisters recipents for stanzas.
        
        ``handler`` instance of an object that defines at least
        one method with the expected properties.
        """
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

    def unregister_all(self):
        """
        Unregisters all previously registered handler.

        Note that this is done automatically when `terminated` is called.
        """
        for handler in self.handlers:
            self.unregister(handler)
        
    def swap_handler(self, new_handler, name, ns, once=False, forget=True):
        """
        Swap an existing handler with a new one.

        ``new_handler`` callable to use from now on. It must accept
        a :class:`bridge.Element` instance as its argument.

        ``name`` stanza name

        ``ns`` stanza namespace

        ``once`` False - flag indicating if the handler should be
        unregistered automatically once it has been called

        ``forget`` True - flag indicating if the dispatched stanza
        should be removed from memory once the handler has been called
        """
        self.parser.unregister_on_element(name, ns)
        p = partial(self.wrap_handler, handler=new_handler, fire_once=once, forget=forget)
        self.parser.register_on_element(name, p, ns)

    def wrap_handler(self, e, handler, fire_once, forget):
        """
        Wrapper for any registered XMPP handler.

        This traps a few exception:

        * ``headstock.error.HeadstockStartTLS`` when the TLS has been requested and is
        supported by the server. This then calls ``headstock.client.BaseClient.start_tls``
        to initiate the TLS negociation.

        * ``headstock.error.HeadstockAuthenticationSuccess`` when the authentication
        was successful.

        * ``headstock.error.HeadstockSessionBound`` when the session is
        eventually bound. It automatically sends the initial presence and asks for
        the account's roster. It also calls ``headstock.client.BaseClient.ready`` so
        that registered handlers are notified of the bound session.

        ``e`` :class:`bridge.Element` instance that has been dispatched
        by the XML parser.

        ``handler`` callable applied with the :class:`bridge.Element` instance.
        If another :class:`bridge.Element` instance is returned, it will
        be sent to the server.  You may also return a list of :class:`bridge.Element`
        instances.

        ``fire_once`` flag indicating if the handler should be applied
        only once or for ever.

        ``forget`` flags indicating if the dispatched :class:`bridge.Element` instance
        should be forgotten to free memory it uses.
        """
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
        except HeadstockAvailable:
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
    def send_raw_stanza(self, stanza):
        """
        Sends a stanza already serialized as a XML string.

        ``stanza`` a stanza serialized as a XML string
        """
        raise NotImplemented()

    def start_tls(self):
        """
        Starts the TLS negociation.
        """
        raise NotImplemented()

    def tls_ok(self):
        """
        Called when the TLS negociation is successful.

        Reset the XML parser and sends a new stream header.
        """
        self.parser.reset()
        self.send_stream_header()

    def start(self):
        """
        Starts the client.
        """
        self.running = True

    def stop(self):
        """
        Stops the client by closing the stream.
        """
        self.send_raw_stanza(self.stream.terminate())
            
    def socket_error(self, msg=None):
        """
        Called whenever the socket was on error.
        """
        self.log(traceback=True)
    
    def ready(self):
        """
        Called whenever the session is bound.

        This goes through registered handlers and
        calls their `ready(client)` method if they
        declare one. The argument is the client's instance.
        """
        self.running = True
        for handler in self.handlers:
            if hasattr(handler, 'ready'):
                handler.ready(self)

    def stopping(self):
        """
        Called whenever the client stops but before
        the socket is closed (unless it was on error
        and already closed).

        This goes through registered handlers and
        calls their `stopping()` method if they
        declare one.
        """
        self.running = False
        for handler in self.handlers:
            if hasattr(handler, 'stopping'):
                handler.stopping()

    def cleanup(self):
        """
        Called after the socket was closed.

        This goes through registered handlers and
        calls their `cleanup()` method if they
        declare one.
        """
        self.log("Cleaning up before terminating the XMPP client")
        for handler in self.handlers:
            if hasattr(handler, 'cleanup'):
                handler.cleanup()
                
    def terminated(self):
        """
        Called right before the client terminates.

        This goes through registered handlers and
        calls their `terminated()` method if they
        declare one and then unregister them.
        """
        self.log("XMPP client terminated")
        for handler in self.handlers:
            if hasattr(handler, 'terminated'):
                handler.terminated()
                self.unregister(handler)
        self.handlers = []

        if self.logger:
            self.logger.close()
            self.logger = None


class AsyncClient(asyncore.dispatcher, BaseClient):
    def __init__(self, jid, password, hostname='localhost', port=5222, tls=False, registercls=None):
        asyncore.dispatcher.__init__(self)
        #delattr(asyncore.dispatcher, 'log')
        
        BaseClient.__init__(self, jid, password, tls, registercls)
        
        self.buffer = ""

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((hostname, port))

    def log(self, stanza=None, prefix='', traceback=False):
        BaseClient.log(self, stanza, prefix, traceback)
        
    def send_raw_stanza(self, stanza):
        BaseClient.log(self, stanza, 'OUTGOING')
        self.buffer += stanza

    def start_tls(self):
        assert ssl, "Python 2.6+ and OpenSSL required for SSL"
        self.socket = ssl.wrap_socket(self.socket, server_side=False)
        self.tls_ok()

    def start(self):
        self.running = True
        self.run(start_loop=False)
        
    def stop(self):
        self.stopping()
        
        if self.connected:
            BaseClient.stop(self)
            self.close()

        self.cleanup()

        self.terminated()

    def run(self, start_loop=True):
        """
        Starts the client.

        ``start_loop`` True - flag indicating if the
        :func:`asyncore.loop` function should be called too.
        """
        header = self.stream.stream_header()
        self.send_raw_stanza(header)
        
        if start_loop:
            asyncore.loop(use_poll=True)
        
    def writable(self):
        return len(self.buffer) > 0

    def handle_connect(self):
        pass

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
        Inboxes = {"inbox"      : "Incoming data read from the socket",
                   "tcp-control": "Errors bubbling up from the TCPClient component",
                   "tlssuccess" : "If the TLS exchange has succeeded",
                   "control"    : "Shutdown the client stream"}

        Outboxes = {"outbox"  : "",
                    "signal"  : "Shutdown signal",
                    "starttls": "Initiates the TLS negociation"}

        def __init__(self, jid, password, hostname='localhost', port=5222, tls=False, registercls=None):
            super(KamaeliaClient, self).__init__()
            BaseClient.__init__(self, jid, password, tls, registercls)

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
            """
            Starts the client by activating the component.
            """
            self.running = True
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
        def __init__(self, jid, password, hostname='localhost', port=5222, tls=False, registercls=None):
            BaseClient.__init__(self, jid, password, tls, registercls)
            
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
            self.running = True
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
            """
            Starts the client.
            
            ``start_loop`` True - flag indicating if the
            :func:`ioloop.IOLoop.start` method should be called too.
            """
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
