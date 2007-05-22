#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.core.iq import Iq
from headstock.lib.utils import generate_unique
from headstock.protocol.core.stanza import StanzaError
from headstock.protocol.core import Entity
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_SI_NS, XMPP_SI_FILE_TRANSFER_NS, \
     XMPP_FEATURE_NEG_NS

__all__ = ['SI']

#####################################################################################
# Defined in XEP-0095
#####################################################################################
class SI(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)

    ############################################
    # Dispatchers registry
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('si', self._proxy_dispatcher,
                                         namespace=XMPP_SI_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('si', namespace=XMPP_SI_NS)
            
    def _proxy_dispatcher(self, e):
        key = 'si'
        profile = e.get_attribute('profile')
        if profile:
            key = 'si.%s' % unicode(profile)
            self.proxy_registry.dispatch(key, self, e)
        else:
            self.proxy_registry.dispatch(key, self, e)

    def register_default(self, handler):
        self.proxy_registry.add_dispatcher('si', handler)

    def register_on_file_transfer(self, handler):
        self.register_on_profile(XMPP_SI_FILE_TRANSFER_NS, handler)
        
    def register_on_profile(self, namespace, handler):
        self.proxy_registry.add_dispatcher('si.%s' % namespace, handler)

    ############################################
    # Class API
    ############################################
    def create_no_valid_stream(cls, from_jid, to_jid, stanza_id=None):
        iq = Iq.create_error_iq(from_jid=from_jid, to_jid=to_jid,
                                stanza_id=stanza_id)
        error = StanzaError._create_error(u'bad-request', u'cancel',
                                          legacy=u'400', parent=iq)
        E(u'no-valid-streams', namespace=XMPP_SI_NS, parent=error)
        return iq
    create_no_valid_stream = classmethod(create_no_valid_stream)
    
    def create_profile_not_understood(cls, from_jid, to_jid, stanza_id=None):
        iq = Iq.create_error_iq(from_jid=from_jid, to_jid=to_jid,
                                stanza_id=stanza_id)
        error = StanzaError._create_error(u'bad-request', u'modify',
                                          legacy=u'400', parent=iq)
        E(u'bad-profile', namespace=XMPP_SI_NS, parent=error)
        return iq
    create_profile_not_understood = classmethod(create_profile_not_understood)
    
    def create_forbidden(cls, from_jid, to_jid, text=None, stanza_id=None):
        iq = Iq.create_error_iq(from_jid=from_jid, to_jid=to_jid,
                                stanza_id=stanza_id)
        StanzaError._create_error(u'forbidden', u'cancel',
                                  legacy=u'403', text=text, parent=iq)
        return iq
    create_forbidden = classmethod(create_forbidden)

    def create_accept_stream_initiation(cls, from_jid, to_jid, profile, stanza_id=None):
        iq = Iq.create_result_iq(from_jid=from_jid, to_jid=to_jid,
                                 stanza_id=stanza_id)
        si = E(u'si',  namespace=XMPP_SI_NS, parent=iq)
        feat = E(u'feature', namespace=XMPP_FEATURE_NEG_NS, parent=si)
        field = E(u'field', attributes={u'var': u'stream-method'},
                  namespace=XMPP_FEATURE_NEG_NS, parent=feat)
        option = E(u'option', namespace=XMPP_FEATURE_NEG_NS, parent=field)
        E(u'value', content=profile, namespace=XMPP_FEATURE_NEG_NS, parent=option)
        
        return iq
    create_accept_stream_initiation = classmethod(create_accept_stream_initiation)
