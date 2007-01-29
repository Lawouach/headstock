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

from headstock.core.iq import Iq
from headstock.core.jid import JID
from headstock.core.stanza import Stanza
from headstock.core.message import Message
from headstock.error import Error, HeadstockStreamError
from headstock.lib.auth.digest import compute_digest_response
from headstock.lib.registry import Registry
from headstock.lib.utils import generate_unique

__all__ = ['Stream']

class Stream(object):
    operations = ('connected', 'authenticated')
    
    def __init__(self, node_name, client=None, resource_name=None):
        self.node_name = node_name
        self.client = client
        self.resource_name = resource_name
        self.registry = Registry()
        self.error_handler = Error(self.registry)

    def set_registry(self, registry):
        self.registry = registry
        self.error_handler.registry = registry

    def set_auth(self, username, password):
        self.username = username
        self.password = password

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
        response = self.client.communicate(data)
        response = response + '</stream:stream>'
        e = self.parse(response)

        return data

    def _perform_auth(self):
        auth = E(u'auth', attributes={u'mechanism': u'DIGEST-MD5'}, namespace=XMPP_SASL_NS)
        response = self.client.communicate(auth.xml(omit_declaration=True))
        e = self.parse(response)[0]
        
        digest_uri = 'xmpp/%s' % self.node_name
        digest_response = compute_digest_response(e.xml_text, self.username,
                                                  self.password, digest_uri=digest_uri)

        response = E(u'response', content=digest_response, namespace=XMPP_SASL_NS)
        response = self.client.communicate(response.xml(omit_declaration=True))

        e = self.parse(response)

        return e

    def _bind_to_resource(self):
        iq = Iq.create_set_iq(stanza_id=generate_unique()).to_bridge()
        bind = E(u'bind', namespace=XMPP_BIND_NS, parent=iq)
        if self.resource_name is not None:
            E(u'resource', content=self.resource_name,
              namespace=XMPP_BIND_NS, parent=bind)

        response = self.client.communicate(iq.xml(omit_declaration=True))

        e = self.parse(response, as_attribute=xmpp_bind_as_attr)

        return JID.parse(e[0].bind.jid.xml_text), e

    def _create_session(self):
        iq = Iq.create_set_iq(stanza_id=generate_unique()).to_bridge()
        session = E(u'session', namespace=XMPP_SESSION_NS, parent=iq)
        response = self.client.communicate(iq.xml(omit_declaration=True))
        e = self.parse(response)

        return e

    def _disco(self):
        presence = E(u'presence', namespace=XMPP_CLIENT_NS)
        data = presence.xml(omit_declaration=True)

        iq = Iq.create_get_iq(to_jid=self.node_name, stanza_id=generate_unique()).to_bridge()
        query = E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        data = data + iq.xml(omit_declaration=True)

        response = self.client.communicate(data)
        e = self.parse(response)

        return e

    def initiate(self):
        """
        Initiates the stream exchange with the remote component service
        """
        self.client.connect()

        try:
            self._send_stream_header()
            self._perform_auth()
            self._send_stream_header()
            jid, e = self._bind_to_resource()
            self._create_session()
            self._disco()
        except:
            self.terminate()
            raise

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
        return self.client.communicate(data)
    
    def terminate(self):
        """
        Terminates the exchange with the remote service component
        Sends a closing </stream:stream> and closes the underlying
        connection.
        """
        if self.client is not None:
            self.client._send('</stream:stream>')
            self.client.disconnect()


    def parse(self, response, **kwargs):
        """
        Loads the response into a list of bridge.Element instances
        If it fails it calls the 'error' handler with the raw
        response string and then raises HeadstockStreamError.

        The returned value is a list of Element instances because the
        response string can contain many elements at once.
        """

        print response
        elements = []
        try:
            elements.append(E.load(response, **kwargs).xml_root)
        except:
            try:
                # maybe we have several documents at once
                # in the response
                response = '<dummy xmlns="">%s</dummy>' % response
                e = E.load(response, **kwargs).xml_root
                for child in e.xml_children:
                    if isinstance(child, E):
                        elements.append(child)
            except:
                raise HeadstockStreamError, response

        return elements

    def odispatch(self, elements, response, *args, **kwargs):
        """
        Dispatches a response to handlers provided via the registry
        Steps followed by this method:
        1. It looks up for an error element within the response
           If any is found it applies the according handler

        2. If no error element was found it runs the attached handler
           by passing the bridge element, the raw response and *args, **kwargs

        3. Returns the handler returned value if any, None otherwise

        Keyword arguments:
        elements -- list of instances of a brigde.Element as returned by the
        parse method for instance
        response -- raw response string in case the handler needs it
        operation -- if provided tells which handler should be called

        Any trailing args and kwargs will be passed to the handler
        """
        l = iter(elements)
        try:
            for element in l.next():
                #for element in elements:
                got_error = Stanza.is_error(element)
                if got_error:
                    error_element = Stanza.find_error_element(self.error_handler, element)
                    self.error_handler.apply_error_handler(error_element, response)
                else:
                    self.registry.run(element.xml_name, element, response, *args, **kwargs)
        except StopIteration:
            pass
