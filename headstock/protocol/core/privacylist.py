#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.core.stanza import Stanza
from headstock.protocol.core import Entity
from headstock.protocol.core.iq import Iq
from headstock.lib.utils import generate_unique

#####################################################################################
# See section 10 of RFC 3921
#####################################################################################

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_PRIVACY_LIST_NS

__all__ = ['PrivacyList']

class PrivacyList(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)

    ############################################
    # Dispatchers registry
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('query', self._proxy_dispatcher,
                                         namespace=XMPP_PRIVACY_LIST_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('query', namespace=XMPP_PRIVACY_LIST_NS)
            
    def _proxy_dispatcher(self, e):
        key = 'privacy_list'
        iq_parent = e.xml_parent
        iq_type = iq_parent.get_attribute(u'type')
        if iq_type:
            key = 'privacy_list.%s' % iq_type
        self.proxy_registry.dispatch(key, self, e)
   
    def register_on_list(self, handler):
        self.proxy_registry.add_dispatcher('privacy_list.result', handler)
        
    def register_on_set(self, handler):
        self.proxy_registry.add_dispatcher('privacy_list.set', handler)

    ############################################
    # Class methods
    ############################################
    def retrieve_available_privacy_lists(cls, from_jid, stanza_id=None):
        iq = Iq.create_get_iq(from_jid=from_jid, stanza_id=stanza_id)
        E(u'query', namespace=XMPP_PRIVACY_LIST_NS, parent=iq)
        return iq
    retrieve_available_privacy_lists = classmethod(retrieve_available_privacy_lists)
    
    def retrieve_privacy_list(cls, from_jid, name, stanza_id=None):
        iq = Iq.create_get_iq(from_jid=from_jid, stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_PRIVACY_LIST_NS, parent=iq)
        E(u'list', attributes={u'name': name},
          namespace=XMPP_PRIVACY_LIST_NS, parent=query)
        return iq
    retrieve_privacy_list = classmethod(retrieve_privacy_list)

    def reset_privacy_list(cls, from_jid, name, stanza_id=None):
        iq = Iq.create_set_iq(from_jid=from_jid, stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_PRIVACY_LIST_NS, parent=iq)
        E(u'list', attributes={u'name': name},
          namespace=XMPP_PRIVACY_LIST_NS, parent=query)
        return iq
    reset_privacy_list = classmethod(reset_privacy_list)
