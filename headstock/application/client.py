# -*- coding: utf-8 -*-

import time, sys, Queue
import logging

from headstock.lib.utils import generate_unique
from headstock.protocol.core.stream import Stream
from headstock.api.session import Session

from bridge.parser import DispatchParser

__all__ = ['ThreadedBaseClient']

class ThreadedBaseClient(object):
    def __init__(self, hostname=None, port=5222):
        self.keep_alive = True
        self.hostname = hostname
        self.port = port

        self.client = None
        self.stream = None
        self.session = None

        self.with_tls = False
        self.certificate = None
        self.certificate_key = None
        self.cert_passphrase_cb = None

        self.vinfo = None
        
        self.node_name = None
        self.username = None
        self.password = None
        self.resource_name = None

        self.logger = None

    def set_logger(self, filename=None, stdio_logger=False, name=None):
        if not name:
            from headstock.lib.utils import generate_unique
            name = str(generate_unique)
            
        self.logger = logging.getLogger("headstock.xmpp.client.%s.logger" % name)
        self.logger.setLevel(logging.DEBUG)
        
        logfmt = logging.Formatter("[%(asctime)s] %(message)s")

        if filename:
            h = logging.FileHandler(filename)
            h.setLevel(logging.DEBUG)
            h.setFormatter(logfmt)
            self.logger.addHandler(h)

        if stdio_logger:
            h = logging.StreamHandler(sys.stdout)
            h.setLevel(logging.DEBUG)
            h.setFormatter(logfmt)
            self.logger.addHandler(h)

    def set_jid_details(self, node_name, username, password, resource_name=None):
        self.node_name = node_name
        self.username = username
        self.password = password
        self.resource_name = resource_name

    def set_ssl_details(self, cert, cert_key, cert_passphrase_cb):
        self.with_tls = True
        self.certificate = cert
        self.certificate_key = cert_key
        self.cert_passphrase_cb = cert_passphrase_cb
        
    def set_version(self, vinfo):
        self.vinfo = vinfo

    def setup(self):
        from headstock.lib.network.threadedclient import ThreadedClient
        self.client = ThreadedClient(self.hostname, self.port)
        self.client.set_logger(self.logger)
        
        parser = DispatchParser()
        self.client.set_parser(parser)

        self.stream = Stream(self.client)
        self.stream.initialize_all()
        self.stream.register_dispatchers()
        
        self.session = Session(self.stream)
        self.session.initialize_dispatchers()
        
        self.session.error.on_received(self.handle_error)
        self.session.discovery.on_infos_requested(self.info_requested)
        if self.vinfo:
            self.session.version.set(self.vinfo)
            
        self.stream.set_node_name(self.node_name)
        self.stream.set_auth(self.username, self.password)
        self.stream.set_resource_name(self.resource_name)
        if self.with_tls:
            self.client.certificate = self.certificate
            self.client.certificate_key = self.certificate_key
            self.client.certificate_password_cb = self.cert_passphrase_cb
            self.stream.enable_tls()
            
        self.stream.register_on_connected(self.connected)
        self.stream.register_on_authenticated(self.authenticated)
        self.stream.register_on_bound(self.bound)

    def start(self):
        self.log("Connecting to '%s:%d'..." % (self.hostname, self.port))
        self.client.connect()
        
        self.client.start()
        
        self.log("Initiating stream...")
        self.stream.initiate()

        self.loop()

    def stop(self):
        self.log("Terminating stream...")
        self.stream.terminate()
        
        self.log("Disconnecting...")
        self.client.disconnect()
        
        self.log("Disconnected")
        self.client.join()
        
        self.keep_alive = False
        
    def loop(self):
        client = self.client
        parser = client.get_parser()
        while self.keep_alive:
            try:
                data = client.incoming.get(timeout=0.01)
                parser.feed(data)
            except Queue.Empty:
                pass

    def log(self, message):
        if self.logger:
            self.logger.debug("LOG: %s", message)

    ###########################################
    # Should be implemented in your subclasses
    ###########################################
    def handle_error(self, error):
        self.log("%r" % error)

    def connected(self):
        self.log("Connected")

    def authenticated(self):
        self.log("Authenticated")

    def bound(self):
        self.log("Bound")

        # Informs the server that the client is available
        from headstock.protocol.core.presence import Presence
        presence = Presence.create_presence()
        self.stream.propagate(element=presence)

        # Request the roster list to the server
        from headstock.protocol.core.roster import Roster
        iq = Roster.retrieve_roster_list(unicode(self.stream.jid),
                                         stanza_id=generate_unique())
        self.stream.propagate(element=iq)

        from headstock.protocol.core.stream import AVAILABLE
        self.stream.connection_status = AVAILABLE
        
    def info_requested(self, from_jid):
        from headstock.api.discovery import Discovery, Feature, Identity
        from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS, \
             XMPP_OOB_NS, XMPP_SI_NS, XMPP_SI_FILE_TRANSFER_NS, XMPP_BYTESTREAMS_NS
        
        d = Discovery()
        d.identities.append(Identity(category=u'client', type=u'pc'))
        d.features.append(Feature(var=XMPP_DISCO_INFO_NS))
        d.features.append(Feature(var=XMPP_DISCO_ITEMS_NS))
        #d.features.append(Feature(var=XMPP_OOB_NS))
        d.features.append(Feature(var=XMPP_SI_NS))
        #d.features.append(Feature(var=XMPP_SI_FILE_TRANSFER_NS))
        #d.features.append(Feature(var=XMPP_BYTESTREAMS_NS))
        self.session.discovery.send_information(d, to_jid=from_jid)
