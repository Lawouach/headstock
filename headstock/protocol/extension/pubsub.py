#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.core.iq import Iq
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_PUBSUB_NS, XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS
from bridge.common import xmpp_as_attr, xmpp_as_list, xmpp_attribute_of_element

__all__ = ['Service', 'Subscribe']

class Service(object):
    operations = ('item-not-found', 'bad-request')

    def __init__(self, stream, proxy_registry=None):
        self.stream = stream
        self.from_jid = None
        self.to_jid = None
        self.proxy_registry = proxy_registry

    def initialize_dispatchers(self):
        pass

    def cleanup_dispatchers(self):
        pass
    
    def set_jids(self, from_jid, to_jid):
        self.from_jid = from_jid
        self.to_jid = to_jid
    
    def subscribe(self, node_name):
        iq = Iq.create_set_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attributes = {u'node': node_name, u'jid': self.from_jid}
        E(u'subscribe', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        r = self.stream.propagate(element=iq)

        e = self.stream.parse(r, as_attribute=xmpp_as_attr, as_list=xmpp_as_list,
                              as_attribute_of_element=xmpp_attribute_of_element)

        return e

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

    def publish(self, node_name, element=None):
        iq = Iq.create_set_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attributes = {u'node': node_name}
        publish = E(u'publish', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        attributes = {u'id': generate_unique()}
        item = E(u'item', attributes=attributes, namespace=XMPP_PUBSUB_NS, parent=publish)
        if element is not None:
            item.xml_children.append(element)
        
        r = self.stream.propagate(element=iq)

        e = self.stream.parse(r)

        return e
        
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
        
