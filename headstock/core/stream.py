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
     XMPP_BIND_NS, XMPP_SESSION_NS, XMPP_DISCO_ITEMS_NS

from headstock.core.iq import Iq
from headstock.core.message import Message
from headstock.lib.auth.digest import compute_digest_response
from headstock.lib.registry import Registry
from headstock.error import HeadstockStreamError

__all__ = ['Stream']

class Stream(object):
    operations = ('connected', 'authenticated')
    
    def __init__(self, node_name, client=None):
        self.node_name = node_name
        self.client = client
        self.registry = Registry()

    def set_registry(self, registry):
        self.registry = registry

    def set_auth(self, username, password):
        self.username = username
        self.password = password

    def __load(self, response):
        try:
            return E.load(response).xml_root
        except:
            self.registry.run('error', response)
            raise HeadstockStreamError, response

    def __trim_end_tag(self, element):
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
        response = self.client.communicate(data)
        self.registry.run('connected', response)

        return data

    def _perform_auth(self):
        auth = E(u'auth', attributes={u'mechanism': u'DIGEST-MD5'}, namespace=XMPP_SASL_NS)
        response = self.client.communicate(auth.xml(omit_declaration=True))
        e = self.__load(response)
        
        digest_uri = 'xmpp/%s' % self.node_name
        digest_response = compute_digest_response(e.xml_text, self.username,
                                                  self.password, digest_uri=digest_uri)

        response = E(u'response', content=digest_response, namespace=XMPP_SASL_NS)
        response = self.client.communicate(response.xml(omit_declaration=True))
        e = self.__load(response)
        
        if e.xml_name == 'success':
            self.registry.run('authenticated', e, response)
        elif e.xml_name == 'failure':
            self.registry.run('failure', e, response)
            raise HeadstockStreamError, response

    def _bind_to_resource(self):
        iq = Iq.create_set_iq(stanza_id=u'tehe').to_bridge()
        bind = E(u'bind', namespace=XMPP_BIND_NS, parent=iq)
        E(u'resource', content=u'Test', namespace=XMPP_BIND_NS, parent=bind)

        response = self.client.communicate(iq.xml(omit_declaration=True))
        e = self.__load(response)

        jid = e.xml_children[0].xml_children[0]
        return jid.xml_text

    def _create_session(self):
        iq = Iq.create_set_iq(stanza_id=u'tehe').to_bridge()
        session = E(u'session', namespace=XMPP_SESSION_NS, parent=iq)
        response = self.client.communicate(iq.xml(omit_declaration=True))

    def _disco(self):
        presence = E(u'presence', namespace=XMPP_CLIENT_NS)
        data = presence.xml(omit_declaration=True)

        iq = Iq.create_get_iq(to_jid=self.node_name, stanza_id=u'tehe').to_bridge()
        query = E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        data = data + iq.xml(omit_declaration=True)

        response = self.client.communicate(data)

    def initiate(self):
        self.client.connect()

        stream = self._send_stream_header()
        self._perform_auth()
        response = self.client.communicate(stream)
        jid = self._bind_to_resource()
        self._create_session()
        self._disco()

        return jid

    def propagate(self, stanza=None, element=None, data=None):
        """
        Send to the remote host the given stanza.
        Returns the Element instance of the returned response

        Keyword arguments:
        stanza -- a stanza instance (Message, Iq, Presence) (or)
        element -- an Element instance representing a stanza (or)
        data -- an XML string of a stanza
        """
        if stanza:
            data = stanza.to_bridge().xml(omit_declaration=True)
        elif element:
            data = element.xml(omit_declaration=True)
        response = self.client.communicate(data)
        return self.__load(response)
    
    def terminate(self):
        if self.client is not None:
            self.client._send('</stream:stream>')
            self.client.disconnect()
