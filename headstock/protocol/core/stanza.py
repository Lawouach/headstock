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
     XMPP_STANZA_ERROR_NS, XML_NS, XML_PREFIX

__all__ = ['Stanza', 'StanzaError']

class Stanza(object):
    def __init__(self, kind=None, from_jid=None, to_jid=None,
                 type=None, id=None, lang=None):
        self.kind = kind
        self.type = type
        self.to_jid = to_jid
        self.from_jid = from_jid
        self.id = id
        self.lang = lang
        self.children = []

    def __repr__(self):
        return '<Stanza "%s" type="%s" from="%s" to="%s" id="%s" at %s>' % (self.kind, self.type, self.from_jid,
                                                                            self.to_jid, self.id, hex(id(self)))
        
    def to_element(self, parent=None):
        attributes = {}
        if self.type:
            attributes = {u'type': self.type}
        stanza = E(self.kind, attributes=attributes, parent=parent)
        if self.from_jid:
            A(u'from', value=self.from_jid, parent=stanza)
        if self.to_jid:
            A(u'to', value=self.to_jid, parent=stanza)
        if self.id:
            A(u'id', value=self.id, parent=stanza)
        if self.lang:
            A(u'lang', value=self.lang, prefix=XML_PREFIX,
              namespace=XML_NS, parent=stanza)

        stanza.update_prefix(None, None, XMPP_CLIENT_NS, False)
            
        return stanza

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
    def create_as_iq(cls, from_jid, to_jid, condition, type, legacy=None,
                     text=None, lang=None, stanza_id=None, children=None):
        if not stanza_id:
            from headstock.lib.utils import generate_unique
            stanza_id = generate_unique()

        from headstock.protocol.core.iq import Iq
        iq = Iq.create_error_iq(from_jid=from_jid, to_jid=to_jid, stanza_id=stanza_id)
        
        children = children or []
        iq.xml_children.extend(children)

        cls._create_error(iq, condition=condition, type=type,
                          legacy=legacy, text=text, lang=lang)

        return iq
    create_as_iq = classmethod(create_as_iq)
    
    def create_as_presence(cls, from_jid, to_jid, condition, type, legacy=None,
                           text=None, lang=None, stanza_id=None, children=None):
        if not stanza_id:
            from headstock.lib.utils import generate_unique
            stanza_id = generate_unique()

        from headstock.protocol.core.iq import Iq
        iq = Stanza(u'presence', from_jid=from_jid, to_jid=to_jid,
                    stanza_id=stanza_id).to_element()
        
        children = children or []
        iq.xml_children.extend(children)

        cls._create_error(iq, condition=condition, type=type,
                          legacy=legacy, text=text, lang=lang)

        return iq
    create_as_presence = classmethod(create_as_presence)
    
    def create_as_message(cls, from_jid, to_jid, condition, type, legacy=None,
                          text=None, lang=None, stanza_id=None, children=None):
        if not stanza_id:
            from headstock.lib.utils import generate_unique
            stanza_id = generate_unique()

        from headstock.protocol.core.iq import Iq
        iq = Stanza(u'message', from_jid=from_jid, to_jid=to_jid,
                    stanza_id=stanza_id).to_element()
        
        children = children or []
        iq.xml_children.extend(children)

        cls._create_error(iq, condition=condition, type=type,
                          legacy=legacy, text=text, lang=lang)

        return iq
    create_as_message = classmethod(create_as_message)
    
    def _create_error(cls, stanza, condition, type, legacy=None, text=None, lang=None):
        attrs = {u'type': type}
        if legacy:
            attrs[u'code'] = legacy
        error = E(u'error', attributes=attrs,
                  namespace=XMPP_CLIENT_NS, parent=stanza)
        E(condition, namespace=XMPP_STANZA_ERROR_NS,
          parent=error)
        if text:
            text = E(u'text', content=text, parent=error,
                     namespace=XMPP_STANZA_ERROR_NS)
            if lang:
                A(u'lang', value=lang, namespace=XML_NS, parent=text)
    _create_error = classmethod(_create_error)

    @classmethod
    def create_bad_request(cls, from_jid=None, to_jid=None, stanza_id=None,
                           children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'bad-request', u'modify', u'400',
                                        stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_conflict(cls, from_jid=None, to_jid=None, stanza_id=None,
                        children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'conflict', u'cancel', u'409',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_feature_not_implemented(cls, from_jid=None, to_jid=None, stanza_id=None,
                                       children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'feature-not-implemented',
                                         u'cancel', u'501',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_forbidden(cls, from_jid=None, to_jid=None, stanza_id=None,
                         children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'forbidden', u'auth', u'403',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_gone(cls, from_jid=None, to_jid=None, stanza_id=None,
                    children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'gone', u'modify', u'302',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_internal_server_error(cls, from_jid=None, to_jid=None, stanza_id=None,
                                     children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'internal-server-error', u'wait', u'500',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_item_not_found(cls, from_jid=None, to_jid=None, stanza_id=None,
                              children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'item-not-found', u'cancel', u'404',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_jid_malformed(cls, from_jid=None, to_jid=None, stanza_id=None,
                             children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'jid-malformed', u'cancel', u'400',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_not_acceptable(cls, from_jid=None, to_jid=None, stanza_id=None,
                              children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'not-acceptable', u'modify', u'406',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_not_allowed(cls, from_jid=None, to_jid=None, stanza_id=None,
                           children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'not-allowed', u'modify', u'405',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_not_authorized(cls, from_jid=None, to_jid=None, stanza_id=None,
                              children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'not-authorized', u'auth', u'401',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_payment_required(cls, from_jid=None, to_jid=None, stanza_id=None,
                                children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'payment-required', u'auth', u'402',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_recipient_unavailable(cls, from_jid=None, to_jid=None, stanza_id=None,
                                     children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'recipient-unavailable', u'wait', u'404',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_redirect(cls, from_jid=None, to_jid=None, stanza_id=None,
                        children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'redirect', u'modify', u'302',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_registration_required(cls, from_jid=None, to_jid=None, stanza_id=None,
                                     children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'registration-required', u'auth', u'407',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_remote_server_not_found(cls, from_jid=None, to_jid=None, stanza_id=None,
                                       children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'remote-server-not-found', u'cancel', u'404',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_remote_server_timeout(cls, from_jid=None, to_jid=None, stanza_id=None,
                                     children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'remote-server-timeout', u'wait', u'504',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_resource_contraint(cls, from_jid=None, to_jid=None, stanza_id=None,
                                  children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'resource-constraint', u'wait', u'500',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_service_unavailable(cls, from_jid=None, to_jid=None, stanza_id=None,
                                   children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'service-unavailable', u'cancel', u'503',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_subscription_required(cls, from_jid=None, to_jid=None, stanza_id=None,
                                     children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'subscription-required', u'auth', u'407',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
    @classmethod
    def create_undefined_condition(cls, type=u'cancel', text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'undefined-condition', type, u'500',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)

    @classmethod
    def create_unexpected_request(cls, from_jid=None, to_jid=None, stanza_id=None,
                                  children=None, text=None, lang=None):
        return StanzaError.create_as_iq(from_jid, to_jid, u'unexpected-request', u'wait', u'400',
                                         stanza_id=stanza_id, text=text, lang=lang, children=children)
    
