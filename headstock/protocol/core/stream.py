#!/usr/bin/env python
# -*- coding: utf-8 -*-

#####################################################################################
#�From RFC 3920
# An XML stream is a container for the exchange of XML elements between any two
# entities over a network.
#####################################################################################

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_STREAM_NS, XMPP_STREAM_PREFIX,\
     XMPP_SASL_NS, XMPP_SASL_PREFIX, XMPP_AUTH_NS, XMPP_TLS_NS, XMPP_CLIENT_NS, \
     XMPP_BIND_NS, XMPP_SESSION_NS, XMPP_DISCO_ITEMS_NS, xmpp_bind_as_attr

from headstock.protocol.core import Entity
from headstock.protocol.core.message import Message
from headstock.protocol.core.roster import Roster
from headstock.protocol.core.iq import Iq
from headstock.protocol.core.presence import Presence
from headstock.protocol.core.jid import JID
from headstock.protocol.core.stanza import Stanza, StanzaError
from headstock.protocol.core.message import Message

from headstock.error import Error, HeadstockStreamError

from headstock.protocol.extension.discovery import Disco
from headstock.protocol.extension.pubsub import Service
from headstock.protocol.extension.si import SI
from headstock.protocol.extension.version import Version

from headstock.lib.auth.plain import generate_credential
from headstock.lib.auth.gaa import perform_authentication
from headstock.lib.auth.digest import challenge_to_dict, compute_digest_response
from headstock.lib.registry import ProxyRegistry
from headstock.lib.utils import generate_unique

__all__ = ['Stream', 'StreamError', 'SaslError']

_entities = (('presence', Presence),
             ('pubsub', Service),
             ('discovery', Disco),
             ('roster', Roster),
             ('message', Message),
             ('si', SI),
             ('version', Version))

# Connection status
# Each one implies the preceding one to have been reached
DISCONNECTED = 0
CONNECTED = 1
AUTHENTICATED = 2
BOUND = 3

class Stream(object):
    def __init__(self, client=None):
        self.client = client
        self.proxy_registry = ProxyRegistry(self)
        self.stream_error = StreamError(self, self.proxy_registry)
        self.stanza_error = StanzaError(self, self.proxy_registry)
        self.sasl_error = SaslError(self, self.proxy_registry)
        self.jid = None
        self.use_tls = False
        self.node_name = None
        self.connection_status = DISCONNECTED
        
    def get_client(self):
        return self.client

    def set_auth(self, username, password):
        self.username = username
        self.password = password

    def set_resource_name(self, resource_name):
        self.resource_name = resource_name

    def set_node_name(self, node_name):
        self.node_name = node_name

    def enable_tls(self):
        self.use_tls = True

    def initialize_all(self, apart_from=None):
        self.stream_error.initialize_dispatchers()
        self.stanza_error.initialize_dispatchers()
        self.sasl_error.initialize_dispatchers()
        
        apart_from = apart_from or []
        for (name, cls) in _entities:
            if name not in apart_from:
                entity = cls(self, self.proxy_registry)
                try:
                    entity.initialize_dispatchers()
                except NotImplemented:
                    pass
                setattr(self, name, entity)

    def register_on_connected(self, handler):
        self._on_connected = handler
        
    def register_on_authenticated(self, handler):
        self._on_authenticated = handler
        
    def register_on_bound(self, handler):
        self._on_bound = handler
               
    def __trim_end_tag(self, element, omit_decl=False):
        """
        The stream element is sent opened. We trim the closing tag
        manually.
        """
        xmlstr = element.xml(indent=False, omit_declaration=omit_decl).strip()
        if xmlstr[-2:] == '/>':
            return '%s>' % xmlstr[:-2].rstrip()
        
        if element.xml_prefix:
            token = '</%s:%s>' % (element.xml_prefix, element.xml_name)
        else:
            token = '</%s>' % element.xml_name

        pos = 0 - len(token)
        return xmlstr[:pos]

    def _send_stream_header(self, omit_decl=False):
        attributes = {u'to': self.node_name, u'version': u'1.0',
                      u'id': generate_unique()}
        stream = E(u'stream', attributes=attributes,
                   prefix=XMPP_STREAM_PREFIX, namespace=XMPP_STREAM_NS)

        A(u'xmlns', value=XMPP_CLIENT_NS, parent=stream)

        data = self.__trim_end_tag(stream, omit_decl)
        self.propagate(data=data)

    def _reset_stream_header(self, omit_decl=False):
        self.connection_status = CONNECTED
        parser = self.client.get_parser()
        parser.reset()
        self._send_stream_header(omit_decl)

    def _handle_features(self, e):
        mechanisms = e.get_child('mechanisms', ns=XMPP_SASL_NS)
        support_tls = e.get_child('starttls', ns=XMPP_TLS_NS)
        if support_tls and self.use_tls:
            parser = self.client.get_parser()
            parser.register_on_element('proceed', namespace=XMPP_TLS_NS,
                                        dispatcher=self._handle_tls)
            tls = E(u'starttls', namespace=XMPP_TLS_NS)
            self.propagate(element=tls)
        elif mechanisms:
            self._handle_mechanisms(mechanisms)
            
    def _handle_tls(self, e):
        self.client.start_tls()
        self._reset_stream_header(omit_decl=True)

    def _handle_mechanisms(self, e):
        mechanisms = [m.xml_text for m in e.xml_children]
        mechanism = None

        # Always favour DIGEST-MD5 if supported by receiving entity
        if u'DIGEST-MD5' in mechanisms:
            mechanism = u'DIGEST-MD5'
            token = None
        elif u'PLAIN' in mechanisms:
            mechanism = u'PLAIN'
            email = '%s@%s' % (self.username, self.node_name)
            token = generate_credential(email, self.username, self.password)
        elif u'X-GOOGLE-TOKEN' in mechanisms:
            mechanism = u'X-GOOGLE-TOKEN'
            token = perform_authentication(self.username, self.password)
        elif u'ANONYMOUS' in mechanisms:            
            mechanism = u'ANONYMOUS'
            token = None
        else:
            # We don't support any of the proposed mechanism
            # let's abort the SASL exchange
            auth = E(u'abort', namespace=XMPP_SASL_NS)
            self.propagate(element=auth)
            return
            
        auth = E(u'auth', content=token,
                 attributes={u'mechanism': mechanism},
                 namespace=XMPP_SASL_NS)
        self.propagate(element=auth)
        
    def _handle_challenge(self, e):
        response_token = None
        params = challenge_to_dict(e.xml_text)
        # Handling 'rspauth' token in DIGEST-MD5
        # See section 2.1.3 of RFC 2831
        if 'rspauth' not in params:
            digest_uri = 'xmpp/%s' % self.node_name
            response_token = compute_digest_response(params, self.username,
                                                     self.password, digest_uri=digest_uri)
            
        response = E(u'response', content=response_token, namespace=XMPP_SASL_NS)
        self.propagate(element=response)

    def _handle_authenticated(self, e):
        self.connection_status = AUTHENTICATED
        self._reset_stream_header()

    def _handle_binding(self, e):
        parser = self.client.get_parser()
        parser.unregister_on_element('bind', namespace=XMPP_BIND_NS)
        iq = Iq.create_set_iq(stanza_id=generate_unique())
        bind = E(u'bind', namespace=XMPP_BIND_NS, parent=iq)
        if self.resource_name is not None:
            E(u'resource', content=self.resource_name,
              namespace=XMPP_BIND_NS, parent=bind)

        self.propagate(element=iq)

    def _handle_session(self, e):
        parser = self.client.get_parser()
        parser.unregister_on_element('session', namespace=XMPP_SESSION_NS)
        iq = Iq.create_set_iq(stanza_id=generate_unique())
        session = E(u'session', namespace=XMPP_SESSION_NS, parent=iq)
        self.propagate(element=iq)

    def _handle_jid(self, e):
        parser = self.client.get_parser()
        parser.unregister_on_element('jid', namespace=XMPP_BIND_NS)
        self.jid = JID.parse(e.xml_text)
        
        iq = Roster.retrieve_roster_list(unicode(self.jid), stanza_id=generate_unique())
        self.propagate(element=iq)
        
        self.connection_status = BOUND
        
        presence = Presence.create_presence() #to_jid=self.node_name)
        iq = Iq.create_get_iq(to_jid=self.node_name, stanza_id=generate_unique())
        query = E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        data = presence.xml(indent=False, omit_declaration=True)
        data = data + iq.xml(indent=False, omit_declaration=True)
        self.propagate(data=data)

        if callable(self._on_bound):
            self._on_bound()

    def _disco(self):
        presence = E(u'presence', namespace=XMPP_CLIENT_NS)
        data = presence.xml(omit_declaration=True)

        iq = Disco.create_item_query(to_jid=self.node_name, stanza_id=generate_unique())
        data = data + iq.xml(omit_declaration=True)

        self.propagate(data=data)

    def initiate(self):
        """
        Initiates the stream exchange with the remote component service
        """
        parser = self.client.get_parser()
        parser.register_on_element('features', namespace=XMPP_STREAM_NS,
                                    dispatcher=self._handle_features)
        parser.register_on_element_per_level('challenge', 1, namespace=XMPP_SASL_NS,
                                              dispatcher=self._handle_challenge)
        parser.register_on_element_per_level('success', 1, namespace=XMPP_SASL_NS,
                                              dispatcher=self._handle_authenticated)
        parser.register_on_element('bind', namespace=XMPP_BIND_NS,
                                    dispatcher=self._handle_binding)
        parser.register_on_element('session', namespace=XMPP_SESSION_NS,
                                    dispatcher=self._handle_session)
        parser.register_on_element('jid', namespace=XMPP_BIND_NS,
                                    dispatcher=self._handle_jid)
        self._send_stream_header()

    def propagate(self, data=None, element=None):
        """
        Send to the remote host the given stanza.
        Returns the Element instance of the returned response

        Keyword arguments:
        data -- a string of data to send as-is
        element -- an Element instance representing a stanza (or)
        """
        if element:
            data = element.xml(indent=False, omit_declaration=True)

        if data:
            self.client.propagate(data)
    
    def terminate(self):
        """
        Terminates the exchange with the remote service component
        Sends a closing </stream:stream>.
        """
        if self.client is not None:
            # Gracefully disconnect
            presence = Presence.create_presence(to_jid=self.node_name,
                                                presence_type=u'unavailable')
            self.propagate(element=presence)
            self.propagate('</stream:stream>')
            
    def shutdown_stream_on_error(self, error):
        if self.client is not None:
            self.propagate(element=error)
            self.propagate('</stream:stream>')
            self.client.disconnect()
        
    ############################################
    # Dispatchers proxying
    ############################################
    
class StreamError(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)
        self.default_dispatcher = None
    
    ############################################
    # Dispatchers proxying
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('error', self._proxy_dispatcher,
                                         namespace=XMPP_STREAM_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('error', namespace=XMPP_STREAM_NS)

    def _proxy_dispatcher(self, e):
        use_default_dispatcher = True
        no_condition_provided = True
        for child in e.xml_children:
            if child.xml_name == u'text':
                continue
            if child.xml_ns == XMPP_STREAM_NS:
                # The <error/> element MUST contain a child element corresponding
                # to one of the defined stanza error conditions defined below;
                no_condition_provided = False
            key = 'stream.error.%s' % child.xml_name
            if self.proxy_registry.has_dispatcher(key):
                self.proxy_registry.dispatch(key, self, e)
                use_default_dispatcher = False
                break

        if no_condition_provided:
            error = E(u'error', namespace=XMPP_STREAM_NS)
            E(u'bad-format', namespace=XMPP_STREAM_NS, parent=error)
            self.stream.shutdown_stream_on_error(error)
            return

        if use_default_dispatcher and callable(self.default_dispatcher):
            self.default_dispatcher(self, e)

    def register_default_dispatcher(self, handler):
        self.default_dispatcher = handler

    def register_bad_format(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.bad_format', handler)
        
    def register_bad_namespace_prefix(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.bad_namespace_prefix', handler)
        
    def register_conflict(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.conflict', handler)
        
    def register_connection_timeout(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.connection_timeout', handler)
        
    def register_host_gone(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.host_gone', handler)
        
    def register_host_unknown(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.host_unknown', handler)
        
    def register_improper_addressing(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.improper_addressing', handler)
        
    def register_internal_server_error(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.internal_server_error', handler)
        
    def register_invalid_form(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.invalid_form', handler)
        
    def register_invalid_id(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.invalid_id', handler)
        
    def register_invalid_namespace(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.invalid_namespace', handler)
        
    def register_invalid_xml(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.invalid_xml', handler)
        
    def register_not_authorized(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.not_authorized', handler)
        
    def register_policy_violation(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.policy_violation', handler)
        
    def register_remote_connection_failed(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.remote_connection_failed', handler)
        
    def register_resource_constraint(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.resource_constraint', handler)
        
    def register_restricted_xml(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.restricted_xml', handler)
        
    def register_see_other_host(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.see_other_host', handler)
        
    def register_system_shutdown(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.system_shutdown', handler)
        
    def register_undefined_condition(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.undefined_condition', handler)
        
    def register_unsupported_encoding(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.unsupported_encoding', handler)
        
    def register_unsupported_stanza_type(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.unsupported_stanza_type', handler)
        
    def register_unsupported_version(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.unsupported_version', handler)
        
    def register_xml_not_well_formed(self, handler):
        self.proxy_registry.add_dispatcher('stream.error.xml_not_well_formed', handler)
        
class SaslError(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)
        self.default_dispatcher = None
        
    ############################################
    # Dispatchers proxying
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('failure', self._proxy_dispatcher,
                                         namespace=XMPP_SASL_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('failure', namespace=XMPP_SASL_NS)

    def _proxy_dispatcher(self, e):
        use_default_dispatcher = True
        for child in e.xml_children:
            key = 'sasl.error.%s' % child.xml_name
            if self.proxy_registry.has_dispatcher(key):
                self.proxy_registry.dispatch(key, self, e)
                use_default_dispatcher = False
                break

        if use_default_dispatcher and callable(self.default_dispatcher):
            self.default_dispatcher(self, e)

    def register_default_dispatcher(self, handler):
        self.default_dispatcher = handler

    def register_aborted(self, handler):
        self.proxy_registry.add_dispatcher('sasl.error.aborted', handler)
        
    def register_incorrect_encoding(self, handler):
        self.proxy_registry.add_dispatcher('sasl.error.incorrect_encoding', handler)
        
    def register_invalid_authzid(self, handler):
        self.proxy_registry.add_dispatcher('sasl.error.invalid_authzid', handler)
        
    def register_invalid_mechanism(self, handler):
        self.proxy_registry.add_dispatcher('sasl.error.invalid_mechanism', handler)
        
    def register_mechanism_to_weak(self, handler):
        self.proxy_registry.add_dispatcher('sasl.error.mechanism_to_weak', handler)
        
    def register_not_authorized(self, handler):
        self.proxy_registry.add_dispatcher('sasl.error.not_authorized', handler)
        
    def register_not_temporary_auth_failure(self, handler):
        self.proxy_registry.add_dispatcher('sasl.error.temporary_auth_failure', handler)
        
