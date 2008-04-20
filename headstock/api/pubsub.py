#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Node']

from headstock.lib.utils import generate_unique
from headstock.api import Entity
from headstock.api.error import Error
from headstock.protocol.core.jid import JID
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_STREAM_NS, \
    XMPP_PUBSUB_NS, XMPP_PUBSUB_OWNER_NS, XMPP_PUBSUB_NODE_CONFIG_NS

class Configure(object):
    def __init__(self, data=None):
        self.data = data

    def create_leaf_node_whitelist(cls):
        d = Data(form_type=u'submit')
        f = Field(field_type=u'hidden', var=u'FORM_TYPE')
        f.values.append(XMPP_PUBSUB_NODE_CONFIG_NS)
        d.fields.append(f)

        f = Field(var=u'pubsub#access_model')
        f.values.append(u'whitelist')
        d.fields.append(f)
        return Configure(d)
    create_leaf_node_whitelist = classmethod(create_leaf_node_whitelist)

class Item(object):
    def __init__(self, id=None, payload=None):
        self.id = id
        self.payload = payload

    def __repr__(self):
        return '<Item "%s" at %s>' % (self.id or '', hex(id(self)),)
    

class Node(Entity):
    def __init__(self, from_jid, to_jid, node_name=None, type=u'set', stanza_id=None, **kwargs):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id) 
        self.node_name = node_name
        if kwargs:
            self.__dict__.update(kwargs)

    def __repr__(self):
        return '<Node "%s" at %s>' % (self.node_name, hex(id(self)))

    @staticmethod
    def to_creation_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attrs = {u'node': e.node_name}
        E(u'create', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        E(u'configure', namespace=XMPP_PUBSUB_NS, parent=pubsub)
        return iq

    @staticmethod
    def from_creation_element(e):
        node = Node(JID.parse(e.get_attribute_value('from')),
                    JID.parse(e.get_attribute_value('to')),
                    type=e.get_attribute_value('type'),
                    stanza_id=e.get_attribute_value('id'))

        for i in e.xml_children:
            if i.xml_ns in [XMPP_PUBSUB_NS]:
                for p in i.xml_children:
                    if p.xml_ns in [XMPP_PUBSUB_NS]:
                        if p.xml_name == 'create':
                            node.node_name = p.get_attribute('node')
            elif i.xml_ns == XMPP_STREAM_NS and i.xml_name == 'error':
                node.error = Error.from_element(i)

        return node

    @staticmethod
    def to_deletion_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_OWNER_NS, parent=iq)
        attrs = {u'node': e.node_name}
        E(u'delete', attributes=attrs, namespace=XMPP_PUBSUB_OWNER_NS, parent=pubsub)
        return iq

    @staticmethod
    def from_deletion_element(e):
        node = Node(JID.parse(e.get_attribute_value('from')),
                    JID.parse(e.get_attribute_value('to')),
                    type=e.get_attribute_value('type'),
                    stanza_id=e.get_attribute_value('id'))

        for i in e.xml_children:
            if i.xml_ns in [XMPP_PUBSUB_NS]:
                for p in i.xml_children:
                    if p.xml_ns in [XMPP_PUBSUB_NS]:
                        if p.xml_name == 'create':
                            node.node_name = p.get_attribute('node')
            elif i.xml_ns == XMPP_STREAM_NS and i.xml_name == 'error':
                node.error = Error.from_element(i)

        return node

    @staticmethod
    def to_subscription_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        sub_jid = e.sub_jid
        attrs = {u'node': e.node_name, u'jid': e.sub_jid}
        E(u'subscribe', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        return iq
        
    @staticmethod
    def from_subscription_element(e):
        sub = Node(JID.parse(e.get_attribute_value('from')),
                   JID.parse(e.get_attribute_value('to')),
                   type=e.get_attribute_value('type'),
                   stanza_id=e.get_attribute_value('id'))

        for i in e.xml_children:
            if i.xml_ns in [XMPP_PUBSUB_NS]:
                for p in i.xml_children:
                    if p.xml_ns in [XMPP_PUBSUB_NS]:
                        if p.xml_name == 'subscribe':
                            sub.node_name = p.get_attribute('node')
                            sub.sub_jid = p.get_attribute('jid')
            elif i.xml_ns == XMPP_STREAM_NS and i.xml_name == 'error':
                sub.error = Error.from_element(i)

        return sub

    @staticmethod
    def to_unsubscription_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        sub_jid = e.sub_jid
        attrs = {u'node': e.node_name, u'jid': e.sub_jid}
        E(u'unsubscribe', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        return iq
        
    @staticmethod
    def from_unsubscription_element(e):
        sub = Node(JID.parse(e.get_attribute_value('from')),
                   JID.parse(e.get_attribute_value('to')),
                   type=e.get_attribute_value('type'),
                   stanza_id=e.get_attribute_value('id'))

        for i in e.xml_children:
            if i.xml_ns in [XMPP_PUBSUB_NS]:
                for p in i.xml_children:
                    if p.xml_ns in [XMPP_PUBSUB_NS]:
                        if p.xml_name == 'subscribe':
                            sub.node_name = p.get_attribute('node')
                            sub.sub_jid = p.get_attribute('jid')
            elif i.xml_ns == XMPP_STREAM_NS and i.xml_name == 'error':
                sub.error = Error.from_element(i)

        return sub

    @staticmethod
    def to_publication_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attrs = {u'node': e.node_name}
        publish = E(u'publish', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        attrs = {u'id': e.item.id}
        item = E(u'item', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=publish)

        if e.item.payload:
            e.item.payload.xml_parent = item
            item.xml_children.append(e.item.payload)
        return iq
        
    @staticmethod
    def from_publication_element(e):
        node = Node(JID.parse(e.get_attribute_value('from')),
                    JID.parse(e.get_attribute_value('to')),
                    type=e.get_attribute_value('type'),
                    stanza_id=e.get_attribute_value('id'))

        for i in e.xml_children:
            if i.xml_ns in [XMPP_PUBSUB_NS]:
                for p in i.xml_children:
                    if p.xml_ns in [XMPP_PUBSUB_NS]:
                        if p.xml_name == 'publish':
                            node.node_name = p.get_attribute('node')
                            for q in p.xml_children:
                                if q.xml_name == 'item':
                                    payload = None
                                    if q.xml_children:
                                        payload = q.xml_children[0].clone()
                                    node.item = Item(q.get_attribute('id'), payload)                                    
            elif i.xml_ns == XMPP_STREAM_NS and i.xml_name == 'error':
                node.error = Error.from_element(i)

        return node

    @staticmethod
    def to_retract_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attrs = {u'node': e.node_name}
        publish = E(u'retract', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        attrs = {u'id': e.item.id}
        item = E(u'item', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=publish)

        return iq

    @staticmethod
    def from_retract_element(e):
        node = Node(JID.parse(e.get_attribute_value('from')),
                    JID.parse(e.get_attribute_value('to')),
                    type=e.get_attribute_value('type'),
                    stanza_id=e.get_attribute_value('id'))

        for i in e.xml_children:
            if i.xml_ns in [XMPP_PUBSUB_NS]:
                for p in i.xml_children:
                    if p.xml_ns in [XMPP_PUBSUB_NS]:
                        if p.xml_name == 'retract':
                            node.node_name = p.get_attribute('node')
                            for q in p.xml_children:
                                if q.xml_name == 'item':
                                    node.item = Item(q.get_attribute('id'))                                    
            elif i.xml_ns == XMPP_STREAM_NS and i.xml_name == 'error':
                node.error = Error.from_element(i)

        return node
        
    
class Items(object):
    def __init__(self, max_items=None, node=None, subid=None):
        self.max_items = max_items
        self.node = node
        self.subid = subid
        self.items = []
        
    def __repr__(self):
        return '<Items "%s" on (%s) at %s>' % (self.subid or '', self.node, hex(id(self)),)
    
