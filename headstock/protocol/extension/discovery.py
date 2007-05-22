#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.core.iq import Iq
from headstock.lib.utils import generate_unique
from headstock.protocol.core import Entity
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS

__all__ = ['Disco']

#####################################################################################
# Defined in XEP-0030
#####################################################################################
class Disco(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)

    ############################################
    # Dispatchers registry
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('query', self._proxy_dispatcher,
                                         namespace=XMPP_DISCO_INFO_NS)
            self.proxy_registry.register('query', self._proxy_dispatcher,
                                         namespace=XMPP_DISCO_ITEMS_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('query', namespace=XMPP_DISCO_INFO_NS)
            self.proxy_registry.cleanup('query', namespace=XMPP_DISCO_ITEMS_NS)
            
    def _proxy_dispatcher(self, e):
        key = 'disco'
        iq_parent = e.xml_parent
        iq_type = iq_parent.get_attribute(u'type')
        if iq_type:
            key = 'disco.%s' % iq_type
        self.proxy_registry.dispatch(key, self, e)

    def register_on_list(self, handler):
        self.proxy_registry.add_dispatcher('disco.result', handler)
        
    def register_on_set(self, handler):
        self.proxy_registry.add_dispatcher('disco.set', handler)
        
    def register_on_get(self, handler):
        self.proxy_registry.add_dispatcher('disco.get', handler)

    ############################################
    # Class API
    ############################################
    def create_info_query(cls, from_jid, to_jid, stanza_id=None, node_name=None):
        iq = Iq.create_get_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_DISCO_INFO_NS, parent=iq)
        if node_name is not None:
            A(u'node', value=node_name, parent=query)

        return iq
    create_info_query = classmethod(create_info_query)
    
    def create_result_info_query(cls, from_jid, to_jid, stanza_id=None, node_name=None):
        iq = Iq.create_result_iq(from_jid=from_jid, to_jid=to_jid,
                                 stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_DISCO_INFO_NS, parent=iq)
        if node_name is not None:
            A(u'node', value=node_name, parent=query)

        return iq
    create_result_info_query = classmethod(create_result_info_query)

    def create_item_query(cls, from_jid, to_jid, stanza_id=None, node_name=None):
        iq = Iq.create_get_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        if node_name is not None:
            A(u'node', value=node_name, parent=query)

        return iq
    create_item_query = classmethod(create_item_query)

    def create_result_item_query(cls, from_jid, to_jid, stanza_id=None, node_name=None):
        iq = Iq.create_result_iq(from_jid=from_jid, to_jid=to_jid,
                                 stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        if node_name is not None:
            A(u'node', value=node_name, parent=query)

        return iq
    create_result_item_query = classmethod(create_result_item_query)
