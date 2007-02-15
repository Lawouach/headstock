#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.core.iq import Iq
from headstock.lib.utils import generate_unique
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS

__all__ = ['Disco']

class Disco(object):
    def __init__(self, stream, proxy_registry=None):
        self.stream = stream
        self.to_jid = None
        self.from_jid = None
        self.proxy_registry = proxy_registry

    def initialize_dispatchers(self):
        pass
    
    def cleanup_dispatchers(self):
        pass
    
    def set_jids(self, from_jid, to_jid):
        self.from_jid = from_jid
        self.to_jid = to_jid

    def ask_features(self, node_name=None):
        iq = Iq.create_get_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        E(u'query', namespace=XMPP_DISCO_INFO_NS, parent=iq)
        r = self.stream.propagate(element=iq)
        e = self.stream.parse(r)[0]
        q = e.get_child('query', XMPP_DISCO_INFO_NS)        
        query = Query()
        query.from_bridge(q)

        return query.features

    def ask_identities(self, node_name=None):
        iq = Iq.create_get_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        query = E(u'query', namespace=XMPP_DISCO_INFO_NS, parent=iq)
        if node_name is not None:
            A(u'node', value=node_name, parent=query)
        r = self.stream.propagate(element=iq)
        e = self.stream.parse(r)[0]
        
        q = e.get_child('query', XMPP_DISCO_INFO_NS)        
        query = Query()
        query.from_bridge(q)

        return query.identities
    
    def ask_nodes(self, node_name=None):
        iq = Iq.create_get_iq(from_jid=self.from_jid, to_jid=self.to_jid,
                              stanza_id=generate_unique()).to_bridge()
        query = E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        if node_name is not None:
            A(u'node', value=node_name, parent=query)
        r = self.stream.propagate(element=iq)
        e = self.stream.parse(r)[0]

        q = e.get_child('query', XMPP_DISCO_ITEMS_NS)        
        query = Query()
        query.from_bridge(q)

        return query.items

    def fetch_node_metadata(self):
        pass


class Query(object):
    def __init__(self, node=None):
        self.node = node
        self.features = []
        self.identities = []
        self.items = []

    def to_bridge(self, parent=None):
        query = E(u'query', namespace=XMPP_DISCO_INFO_NS, parent=parent)
        if self.node is not None:
            A(u'node', value=self.node, parent=query)

        for feature in self.features:
            feature.to_bridge(parent=query)

        return query

    def from_bridge(self, element):
        self.node = element.get_attribute('node')
        
        identities = element.get_children('identity', XMPP_DISCO_INFO_NS)
        for identity in identities:
            i = Identity()
            i.from_bridge(identity)
            self.identities.append(i)
            
        features = element.get_children('feature', XMPP_DISCO_INFO_NS)
        for feature in features:
            f = Feature()
            f.from_bridge(feature)
            self.features.append(f)
            
        items = element.get_children('item', XMPP_DISCO_ITEMS_NS)
        for item in items:
            i = Item()
            i.from_bridge(item)
            self.features.append(i)
        
class Feature(object):
    def __init__(self, var=None):
        self.var = var

    def to_bridge(self, parent=None):
        attributes = {u'var': self.var}
        feature = E(u'feature', attributes=attributes,
                    namespace=XMPP_DISCO_INFO_NS, parent=parent)

        return feature

    def from_bridge(self, element):
        self.var = element.get_attribute('var').xml_text

class Identity(object):
    def __init__(self, category=None, name=None, type=None):
        self.category = category
        self.name = name
        self.type = type

    def to_bridge(self, parent=None):
        attributes = {u'type': self.type, u'category': self.category}
        identity = E(u'identity', attributes=attributes,
                     namespace=XMPP_DISCO_INFO_NS, parent=parent)

        if self.name:
            A(u'name', value=self.name, parent=identity)

        return identity

    def from_bridge(self, element):
        self.type = element.get_attribute('type').xml_text
        self.category = element.get_attribute('category').xml_text

        self.name = element.get_attribute('name')
        if self.name is not None:
            self.name = self.name.xml_text
        
class Item(object):
    def __init__(self, action=None, jid=None, name=None, node=None):
        if action not in (None, 'remove', 'update'):
            raise ValueError, "action can be 'remove', 'update' or None"
        
        self.action = action
        self.jid = jid
        self.name = name
        self.node = node

    def to_bridge(self, parent=None):
        attributes = {u'jid': self.jid}
        item = E(u'item', attributes=attributes,
                 namespace=XMPP_DISCO_ITEMS_NS, parent=parent)

        if self.action:
            A(u'action', value=self.action,
              namespace=XMPP_DISCO_ITEMS_NS, parent=item)

        if self.name:
            A(u'name', value=self.name,
              namespace=XMPP_DISCO_ITEMS_NS, parent=item)

        if self.node:
            A(u'node', value=self.node,
              namespace=XMPP_DISCO_ITEMS_NS, parent=item)

        return item

    def from_bridge(self, element):
        self.name = element.get_attribute('name')
        if self.name is not None:
            self.name = self.name.xml_text
            
        self.node = element.get_attribute('node')
        if self.node is not None:
            self.node = self.node.xml_text
            
        self.action = element.get_attribute('action')
        if self.action is not None:
            self.action = self.action.xml_text

        self.jid = element.get_attribute('jid').xml_text
