#!/usr/bin/env python
# -*- coding: utf-8 -*-

#####################################################################################
# From RFC 3920
# An XML stanza is a discrete semantic unit of structured information that is sent 
# from one entity to another over an XML stream. 
#####################################################################################

from headstock.error import *
from headstock.core import Entity

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_PUBSUB_NS

__all__ = ['Stanza', 'StanzaError']

class Stanza(object):
    def __init__(self, node_name, from_jid=None, to_jid=None, stanza_type=None, stanza_id=None):
        self.node_name = node_name
        self.from_jid = from_jid
        self.to_jid = to_jid
        self.stanza_id = stanza_id
        self.stanza_type = stanza_type

    def to_bridge(self, parent=None):
        attributes = {}
        if self.stanza_type:
            attributes = {u'type': self.stanza_type}
        stanza = E(self.node_name, attributes=attributes, parent=parent)
        if self.from_jid:
            A(u'from', value=unicode(self.from_jid), parent=stanza)
        if self.to_jid:
            A(u'to', value=unicode(self.to_jid), parent=stanza)
        if self.stanza_id:
            A(u'id', value=self.stanza_id, parent=stanza)

        stanza.update_prefix(None, None, XMPP_CLIENT_NS, False)
            
        return stanza

    def from_bridge(self, element):
        from_jid = element.get_attribute('from')
        if from_jid:
            self.from_jid = from_jid
            
        to_jid = element.get_attribute('to')
        if to_jid:
            self.to_jid = to_jid
            
        stanza_type = element.get_attribute('type')
        if stanza_type:
            self.stanza_type = stanza_type
            
        stanza_id = element.get_attribute('id')
        if stanza_id:
            self.stanza_id = stanza_id 
    
    def xml(self):
        return self.to_bridge().xml(omit_declaration=True)

class StanzaError(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)
        self.default_dispatcher = None
    
    ############################################
    # Dispatchers proxying
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('error', self._proxy_dispatcher,
                                         namespace=XMPP_CLIENT_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('error', namespace=XMPP_CLIENT_NS)

    def _proxy_dispatcher(self, e):
        use_default_dispatcher = True
        for child in e.xml_children:
            if child.xml_name == u'text':
                continue
            key = 'stanza.error.%s' % child.xml_name
            if self.proxy_registry.has_dispatcher(key):
                self.proxy_registry.dispatch(key, self, e)
                use_default_dispatcher = False
                break

        if use_default_dispatcher and callable(self.default_dispatcher):
            self.default_dispatcher(self, e)

    def register_default_dispatcher(self, handler):
        self.default_dispatcher = handler

    def register_bad_request(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.bad_request', handler)
        
    def register_conflict(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.conflict', handler)
        
    def register_feature_not_implemented(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.feature_not_implemented', handler)

    def register_forbidden(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.forbidden', handler)
    
    def register_gone(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.gone', handler)

    def register_internal_server_error(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.internal_server_error', handler)

    def register_item_not_found(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.item_not_found', handler)

    def register_jid_malformed(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.jid_malformed', handler)

    def register_not_acceptable(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.not_acceptable', handler)

    def register_not_not_authorized(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.not_authorized', handler)

    def register_payment_required(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.payment_required', handler)

    def register_recipient_unavailable(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.recipient_unavailable', handler)

    def register_redirect(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.redirect', handler)

    def register_registration_required(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.registration_required', handler)

    def register_remote_server_not_found(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.remote_server_not_found', handler)

    def register_remote_server_timeout(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.remote_server_timeout', handler)

    def register_resource_constraint(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.resource_constraint', handler)

    def register_service_unavailable(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.service_unavailable', handler)

    def register_subscription_required(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.subscription_required', handler)

    def register_undefined_condition(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.undefined_condition', handler)

    def register_unexpected_request(self, handler):
        self.proxy_registry.add_dispatcher('stanza.error.unexpected_request', handler)
