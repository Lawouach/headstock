#!/usr/bin/env python
# -*- coding: utf-8 -*-

#####################################################################################
# From RFC 3920
# An XML stanza is a discrete semantic unit of structured information that is sent 
# from one entity to another over an XML stream. 
#####################################################################################

from headstock.error import *
from headstock.protocol.core import Entity

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_PUBSUB_NS, \
     XMPP_STANZA_ERROR_NS, XML_NS

__all__ = ['Stanza', 'StanzaError']

class Stanza(object):
    def create(cls, node_name, from_jid=None, to_jid=None,
               stanza_type=None, stanza_id=None, parent=None):
        attributes = {}
        if stanza_type:
            attributes = {u'type': stanza_type}
        stanza = E(node_name, attributes=attributes, parent=parent)
        if from_jid:
            A(u'from', value=unicode(from_jid), parent=stanza)
        if to_jid:
            A(u'to', value=unicode(to_jid), parent=stanza)
        if stanza_id:
            A(u'id', value=stanza_id, parent=stanza)

        stanza.update_prefix(None, None, XMPP_CLIENT_NS, False)
            
        return stanza
    create = classmethod(create)

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

    ############################################
    # Class API
    ############################################
    def _create_error(cls, condition, type, legacy=None, text=None, lang=None, parent=None):
        attrs = {u'type': type}
        if legacy:
            attrs[u'code'] = legacy
        error = E(u'error', attributes=attrs,
                  namespace=XMPP_CLIENT_NS, parent=parent)
        E(condition, namespace=XMPP_STANZA_ERROR_NS,
          parent=error)
        if text:
            text = E(u'text', content=text, parent=error,
                     namespace=XMPP_STANZA_ERROR_NS)
            if lang:
                A(u'lang', value=lang, namespace=XML_NS, parent=text)

        return error
    _create_error = classmethod(_create_error)

    @classmethod
    def create_bad_request(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'bad-request', u'modify', u'400',
                                         text, lang, parent)

    @classmethod
    def create_conflict(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'conflict', u'cancel', u'409',
                                         text, lang, parent)

    @classmethod
    def create_feature_not_implemented(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'feature-not-implemented',
                                         u'cancel', u'501',
                                         text, lang, parent)

    @classmethod
    def create_forbidden(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'forbidden', u'auth', u'403',
                                         text, lang, parent)

    @classmethod
    def create_gone(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'gone', u'modify', u'302',
                                         text, lang, parent)

    @classmethod
    def create_internal_server_error(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'internal-server-error', u'wait', u'500',
                                         text, lang, parent)

    @classmethod
    def create_item_not_found(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'item-not-found', u'cancel', u'404',
                                         text, lang, parent)

    @classmethod
    def create_jid_malformed(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'jid-malformed', u'cancel', u'400',
                                         text, lang, parent)

    @classmethod
    def create_not_acceptable(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'not-acceptable', u'modify', u'406',
                                         text, lang, parent)

    @classmethod
    def create_not_allowed(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'not-allowed', u'modify', u'405',
                                         text, lang, parent)

    @classmethod
    def create_not_authorized(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'not-authorized', u'auth', u'401',
                                         text, lang, parent)

    @classmethod
    def create_payment_required(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'payment-required', u'auth', u'402',
                                         text, lang, parent)
    
    @classmethod
    def create_recipient_unavailable(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'recipient-unavailable', u'wait', u'404',
                                         text, lang, parent)
    
    @classmethod
    def create_redirect(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'redirect', u'modify', u'302',
                                         text, lang, parent)
    
    @classmethod
    def create_registration_required(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'registration-required', u'auth', u'407',
                                         text, lang, parent)
    
    @classmethod
    def create_remote_server_not_found(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'remote-server-not-found', u'cancel', u'404',
                                         text, lang, parent)
    
    @classmethod
    def create_remote_server_timeout(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'remote-server-timeout', u'wait', u'504',
                                         text, lang, parent)
    
    @classmethod
    def create_resource_contraint(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'resource-constraint', u'wait', u'500',
                                         text, lang, parent)
    
    @classmethod
    def create_service_unavailable(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'service-unavailable', u'cancel', u'503',
                                         text, lang, parent)
    
    @classmethod
    def create_subscription_required(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'subscription-required', u'auth', u'407',
                                         text, lang, parent)
    
    @classmethod
    def create_undefined_condition(cls, type=u'cancel', text=None, lang=None, parent=None):
        return StanzaError._create_error(u'undefined-condition', type, u'500',
                                         text, lang, parent)

    @classmethod
    def create_unexpected_request(cls, text=None, lang=None, parent=None):
        return StanzaError._create_error(u'unexpected-request', u'wait', u'400',
                                         text, lang, parent)
    
