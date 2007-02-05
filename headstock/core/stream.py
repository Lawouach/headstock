#!/usr/bin/env python
# -*- coding: utf-8 -*-

#####################################################################################
# From RFC 3920
# An XML stream is a container for the exchange of XML elements between any two
# entities over a network.
#####################################################################################

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_STREAM_NS, XMPP_STREAM_PREFIX,\
     XMPP_SASL_NS, XMPP_SASL_PREFIX, XMPP_AUTH_NS, XMPP_TLS_NS, XMPP_CLIENT_NS, \
     XMPP_BIND_NS, XMPP_SESSION_NS, XMPP_DISCO_ITEMS_NS, xmpp_bind_as_attr

from headstock.core.message import Message
from headstock.core.roster import Roster
from headstock.core.iq import Iq
from headstock.core.presence import Presence
from headstock.core.jid import JID
from headstock.core.stanza import Stanza
from headstock.core.message import Message

from headstock.error import Error, HeadstockStreamError

from headstock.extension.discovery import Disco
from headstock.extension.pubsub import Service

from headstock.lib.auth.digest import compute_digest_response
from headstock.lib.registry import ProxyRegistry
from headstock.lib.utils import generate_unique

__all__ = ['Stream']

_entities = (('presence', Presence),
             ('pubsub', Service),
             ('discovery', Disco))

class Stream(object):
    def __init__(self, node_name, client=None):
        self.node_name = node_name
        self.client = client
        self.proxy_registry = ProxyRegistry(self)
        self.jid = None

    def get_client(self):
        return self.client

    def set_auth(self, username, password):
        self.username = username
        self.password = password

    def set_resource_name(self, resource_name):
        self.resource_name = resource_name

    def initialize_all(self, apart_from=None):
        apart_from = apart_from or []
        for (name, cls) in _entities:
            if name not in apart_from:
                entity = cls(self, self.proxy_registry)
                entity.initialize_dispatchers()
                setattr(self, name, entity)
               
    def __trim_end_tag(self, element):
        """
        The stream element is sent opened. We trim the closing tag
        manually.
        """
        xmlstr = element.xml(omit_declaration=True)
        if xmlstr[-2:] == '/>':
            return '%s>' % xmlstr[:-2]
        
        if element.xml_prefix:
            token = '</%s:%s>' % (element.xml_prefix, element.xml_name)
        else:
            token = '</%s>' % element.xml_name

        pos = 0 - len(token)
        return xmlstr[:pos]

    def _send_stream_header(self):
        attributes = {u'to': self.node_name, u'version': u'1.0'}
        stream = E(u'stream', attributes=attributes,
                   prefix=XMPP_STREAM_PREFIX, namespace=XMPP_STREAM_NS)

        A(u'xmlns', value=XMPP_CLIENT_NS, parent=stream)

        data = self.__trim_end_tag(stream)
        self.propagate(data=data)

    def _handle_stream_header(self, e):
        self._perform_auth()

    def _perform_auth(self):
        auth = E(u'auth', attributes={u'mechanism': u'DIGEST-MD5'}, namespace=XMPP_SASL_NS)
        self.propagate(element=auth)

    def _handle_challenge(self, e):
        digest_uri = 'xmpp/%s' % self.node_name
        digest_response = compute_digest_response(e.xml_text, self.username,
                                                  self.password, digest_uri=digest_uri)
        response = E(u'response', content=digest_response, namespace=XMPP_SASL_NS)
        self.propagate(element=response)

    def _handle_authenticated(self, e):
        parser = self.client.get_parser()
        parser.reset()
        self._send_stream_header()

    def _handle_binding(self, e):
        handler = self.client.get_handler()
        handler.unregister_on_element('bind', namespace=XMPP_BIND_NS)
        iq = Iq.create_set_iq(stanza_id=generate_unique())
        bind = E(u'bind', namespace=XMPP_BIND_NS, parent=iq)
        if self.resource_name is not None:
            E(u'resource', content=self.resource_name,
              namespace=XMPP_BIND_NS, parent=bind)

        self.propagate(element=iq)

    def _handle_session(self, e):
        handler = self.client.get_handler()
        handler.unregister_on_element('session', namespace=XMPP_SESSION_NS)
        iq = Iq.create_set_iq(stanza_id=generate_unique())
        session = E(u'session', namespace=XMPP_SESSION_NS, parent=iq)
        self.propagate(element=iq)

    def _handle_jid(self, e):
        handler = self.client.get_handler()
        handler.unregister_on_element('jid', namespace=XMPP_BIND_NS)
        self.jid = JID.parse(e.xml_text)
        
        presence = Presence.create_presence(to_jid=self.node_name)
        iq = Iq.create_get_iq(to_jid=self.node_name, stanza_id=generate_unique())
        query = E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        data = presence.xml(omit_declaration=True)
        data = data + iq.xml(omit_declaration=True)
        self.propagate(data=data)

    def _disco(self):
        presence = E(u'presence', namespace=XMPP_CLIENT_NS)
        data = presence.xml(omit_declaration=True)

        iq = Iq.create_get_iq(to_jid=self.node_name, stanza_id=generate_unique())
        query = E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        data = data + iq.xml(omit_declaration=True)

        self.propagate(data=data)

    def initiate(self):
        """
        Initiates the stream exchange with the remote component service
        """
        handler = self.client.get_handler()
        handler.register_on_element('auth', namespace=u"http://jabber.org/features/iq-auth",
                                    dispatcher=self._handle_stream_header)
        handler.register_on_element_per_level('challenge', 1, namespace=XMPP_SASL_NS,
                                              dispatcher=self._handle_challenge)
        handler.register_on_element_per_level('success', 1, namespace=XMPP_SASL_NS,
                                              dispatcher=self._handle_authenticated)
        handler.register_on_element('bind', namespace=XMPP_BIND_NS,
                                    dispatcher=self._handle_binding)
        handler.register_on_element('session', namespace=XMPP_SESSION_NS,
                                    dispatcher=self._handle_session)
        handler.register_on_element('jid', namespace=XMPP_BIND_NS,
                                    dispatcher=self._handle_jid)
        self._send_stream_header()

    def propagate(self, stanza=None, element=None, data=None):
        """
        Send to the remote host the given stanza.
        Returns the Element instance of the returned response

        Keyword arguments:
        stanza -- a stanza instance (Message, Iq, Presence) (or)
        element -- an Element instance representing a stanza (or)
        data -- a string of data to send as-is
        """
        if stanza:
            data = stanza.to_bridge().xml(omit_declaration=True)
        elif element:
            data = element.xml(omit_declaration=True)
        self.client.propagate(data)
    
    def terminate(self):
        """
        Terminates the exchange with the remote service component
        Sends a closing </stream:stream> and closes the underlying
        connection.
        """
        if self.client is not None:
            # Gracefully disconnect
            presence = Presence.create_presence(to_jid=self.node_name,
                                                presence_type=u'unavailable')
            self.propagate(element=presence)
            self.propagate('</stream:stream>')
            self.client.disconnect()

