#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.core.iq import Iq
from headstock.lib.utils import generate_unique
from headstock.protocol.core import Entity
from headstock.api.dataform import Data

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_PUBSUB_NS, XMPP_DISCO_INFO_NS, \
     XMPP_DISCO_ITEMS_NS, XMPP_PUBSUB_OWNER_NS, XMPP_PUBSUB_EVENT_NS
from bridge.common import xmpp_as_attr, xmpp_as_list, xmpp_attribute_of_element

__all__ = ['Service']

class Service(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)

    ############################################
    # Dispatchers registry
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('pubsub', self._proxy_dispatcher,
                                         namespace=XMPP_PUBSUB_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('pubsub', namespace=XMPP_PUBSUB_NS)
    
    def _proxy_dispatcher(self, e):
        error = e.xml_parent.get_child('error', e.xml_ns)
        iq_type = unicode(e.xml_parent.get_attribute('type'))
        if iq_type == 'error':
            return
        for c in e.xml_children:
            if c.xml_ns == XMPP_PUBSUB_NS:
                key = 'pubsub.%s.%s' % (iq_type, c.xml_name)
                self.proxy_registry.dispatch(key, self, e)

    def register_on_received_subscriptions(self, handler):
        self.proxy_registry.add_dispatcher('pubsub.result.subscriptions', handler)
        
    def register_on_requested_subscriptions(self, handler):
        self.proxy_registry.add_dispatcher('pubsub.get.subscriptions', handler)

    ############################################
    # Class API
    ############################################
    def create_subscriptions(cls, from_jid, to_jid, stanza_id=None,
                             subscriptions=None):
        iq = Iq.create_get_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        sub = E(u'subscriptions', namespace=XMPP_PUBSUB_NS, parent=pubsub)

        return iq
    create_subscriptions = classmethod(create_subscriptions)
    
    def create_affiliations(cls, from_jid, to_jid, stanza_id=None,
                            affiliations=None):
        iq = Iq.create_get_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        sub = E(u'affiliations', namespace=XMPP_PUBSUB_NS, parent=pubsub)

        return iq
    create_affiliations = classmethod(create_affiliations)
        
    def create_subscribe(cls, from_jid, to_jid, jid, node_name, stanza_id=None):
        iq = Iq.create_set_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attributes = {u'node': node_name, u'jid': jid}
        E(u'subscribe', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        return iq
    create_subscribe = classmethod(create_subscribe)

    def create_configure(cls, from_jid, to_jid, node_name, stanza_id=None):
        iq = Iq.create_set_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_OWNER_NS, parent=iq)
        E(u'configure', attributes = {u'node': node_name},
          namespace=XMPP_PUBSUB_OWNER_NS, parent=pubsub)
        return iq
    create_configure = classmethod(create_configure)

    def create_create_node(cls, from_jid, to_jid, node_name, configure=None, stanza_id=None):
        iq = Iq.create_set_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        E(u'create', attributes = {u'node': node_name},
          namespace=XMPP_PUBSUB_NS, parent=pubsub)
        c = E(u'configure', namespace=XMPP_PUBSUB_NS, parent=pubsub)
        if configure:
            Data.to_element(configure.data, parent=c)
        return iq
    create_create_node = classmethod(create_create_node)
    
    def create_delete_node(cls, from_jid, to_jid, node_name, stanza_id=None):
        iq = Iq.create_set_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_OWNER_NS, parent=iq)
        E(u'delete', attributes = {u'node': node_name},
          namespace=XMPP_PUBSUB_OWNER_NS, parent=pubsub)
        return iq
    create_delete_node = classmethod(create_delete_node)

    def create_purge_node(cls, from_jid, to_jid, node_name, stanza_id=None):
        iq = Iq.create_set_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_OWNER_NS, parent=iq)
        E(u'purge', attributes = {u'node': node_name},
          namespace=XMPP_PUBSUB_OWNER_NS, parent=pubsub)
        return iq
    create_purge_node = classmethod(create_purge_node)
    
    def unsubscribe(self, node_name, subid=None):
        iq = Iq.create_set_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attributes = {u'node': node_name, u'jid': self.from_jid}
        sub = E(u'unsubscribe', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        if subid is not None:
            A(u'subid', value=subid, parent=sub)
        r = self.stream.propagate(element=iq)

        e = self.stream.parse(r, as_attribute=xmpp_as_attr, as_list=xmpp_as_list,
                              as_attribute_of_element=xmpp_attribute_of_element)

        return e
        
    def create_node(self, node_name):
        iq = Iq.create_set_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attributes = {u'node': node_name}
        E(u'create', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        E(u'configure', namespace=XMPP_PUBSUB_NS, parent=pubsub)
        r = self.stream.propagate(element=iq)

        e = self.stream.parse(r)

        return e

    def create_publish(cls, from_jid, to_jid, node_name, items_id=None, stanza_id=None):
        iq = Iq.create_set_iq(from_jid=from_jid, to_jid=to_jid, stanza_id=stanza_id)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        publish = E(u'publish', attributes={u'node': node_name},
                    namespace=XMPP_PUBSUB_NS, parent=pubsub)
        attributes = {}
        if items_id:
            attributes = {u'id': generate_unique()}
        item = E(u'item', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=publish)

        return iq, item
    create_publish = classmethod(create_publish)
        
    def delete(self, node_name):
        iq = Iq.create_set_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attributes = {u'node': node_name}
        publish = E(u'delete', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        
        r = self.stream.propagate(element=iq)

        e = self.stream.parse(r)

        return e

    def purge(self, node_name):
        iq = Iq.create_set_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attributes = {u'node': node_name}
        publish = E(u'purge', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        
        r = self.stream.propagate(element=iq)

        e = self.stream.parse(r)

        return e
        
