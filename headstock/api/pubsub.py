#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Node']

from headstock.lib.utils import generate_unique
from headstock.api import Entity
from headstock.api.error import Error
from headstock.api.jid import JID
from headstock.api.dataform import Data, Field
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_STREAM_NS, \
    XMPP_PUBSUB_NS, XMPP_PUBSUB_OWNER_NS, XMPP_PUBSUB_NODE_CONFIG_NS,\
    XMPP_PUBSUB_EVENT_NS, XMPP_SHIM_NS

class Configure(object):
    def __init__(self, x=None):
        self.x = x

    @staticmethod
    def to_element(e, parent=None):
        c = E(u'configure', namespace=XMPP_PUBSUB_NS, parent=parent)
        Data.to_element(e.x, parent=c)
        return c

    @staticmethod
    def make_collection_node():
        d = Data(u'submit')
        d.fields.append(Field(field_type=u'hidden', var=u'FORM_TYPE', 
                               values=[u'http://jabber.org/protocol/pubsub#node_config']))
        d.fields.append(Field(field_type=None, var=u'pubsub#node_type', 
                              values=[u'collection']))
        return Configure(x=d)

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
    def __init__(self, id=None, payload=None, eventType=None):
        self.id = id
        self.payload = payload
        self.event = eventType

    @property
    def name(self):
        return self.id

    def __repr__(self):
        return '<Item "%s" at %s>' % (self.id or '', hex(id(self)),)
    
class Message(Entity):
    def __init__(self, from_jid, to_jid):
        Entity.__init__(self, from_jid, to_jid) 
        self.node_name = None
        self.items = []
        self.event = None

    @staticmethod
    def from_element(e):
        msg = Message(JID.parse(e.get_attribute_value('from')),
                      JID.parse(e.get_attribute_value('to')))

        for c in e.xml_children:
            if c.xml_ns == XMPP_PUBSUB_EVENT_NS: # x or event
                for i in c.xml_children:
                    if i.xml_ns == XMPP_PUBSUB_EVENT_NS: # items
                        msg.node_name = i.get_attribute_value('node')
                        msg.event = i.xml_name
                        if msg.event == 'items':
                            for t in i.xml_children: # item
                                payload = None
                                if t.xml_children:
                                    payload = t.xml_children
                                msg.items.append(Item(id=t.get_attribute_value('id'),
                                                      payload=payload, eventType=t.xml_name))

        return msg

class Node(Entity):
    def __init__(self, from_jid, to_jid, node_name=None, type=u'set', stanza_id=None, **kwargs):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id) 
        self.node_name = node_name
        self.configure = None
        self.subid = None
        if kwargs:
            self.__dict__.update(kwargs)

    def __repr__(self):
        return '<Node "%s" at %s>' % (self.node_name, hex(id(self)))

    def set_default_collection_conf(self):
        self.configure = Configure.make_collection_node()

    @staticmethod
    def to_creation_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attrs = {u'node': e.node_name}
        E(u'create', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        if not e.configure:
            E(u'configure', namespace=XMPP_PUBSUB_NS, parent=pubsub)
        else:
            Configure.to_element(e.configure, parent=pubsub)
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
                            node.node_name = p.get_attribute_value('node')
            elif i.xml_ns == XMPP_CLIENT_NS and i.xml_name == 'error':
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
                            node.node_name = p.get_attribute_value('node')
            elif i.xml_ns == XMPP_CLIENT_NS and i.xml_name == 'error':
                node.error = Error.from_element(i)

        return node

    @staticmethod
    def to_purge_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_OWNER_NS, parent=iq)
        attrs = {u'node': e.node_name}
        E(u'purge', attributes=attrs, namespace=XMPP_PUBSUB_OWNER_NS, parent=pubsub)
        return iq

    @staticmethod
    def from_purge_element(e):
        node = Node(JID.parse(e.get_attribute_value('from')),
                    JID.parse(e.get_attribute_value('to')),
                    type=e.get_attribute_value('type'),
                    stanza_id=e.get_attribute_value('id'))

        for i in e.xml_children:
            if i.xml_ns in [XMPP_PUBSUB_OWNER_NS]:
                for p in i.xml_children:
                    if p.xml_ns in [XMPP_PUBSUB_OWNER_NS]:
                        if p.xml_name == 'purge':
                            node.node_name = p.get_attribute_value('node')                                 
            elif i.xml_ns == XMPP_CLIENT_NS and i.xml_name == 'error':
                node.error = Error.from_element(i)

        return node

    @staticmethod
    def to_subscription_element(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
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
                            sub.node_name = p.get_attribute_value('node')
                            sub.sub_jid = p.get_attribute_value('jid')
            elif i.xml_ns == XMPP_CLIENT_NS and i.xml_name == 'error':
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
                            sub.node_name = p.get_attribute_value('node')
                            sub.sub_jid = p.get_attribute_value('jid')
            elif i.xml_ns == XMPP_CLIENT_NS and i.xml_name == 'error':
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

        if e.item.payload and isinstance(e.item.payload, E):
            e.item.payload.xml_parent = item
            item.xml_children.append(e.item.payload)
        elif e.item.payload and isinstance(e.item.payload, unicode):
            item.xml_text = e.item.payload
            
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
                            node.node_name = p.get_attribute_value('node')
                            for q in p.xml_children:
                                if q.xml_name == 'item':
                                    payload = None
                                    if q.xml_children:
                                        payload = q.xml_children[0].clone()
                                    node.item = Item(q.get_attribute_value('id'), payload)                                    
            elif i.xml_ns == XMPP_CLIENT_NS and i.xml_name == 'error':
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
                            node.node_name = p.get_attribute_value('node')
                            for q in p.xml_children:
                                if q.xml_name == 'item':
                                    node.item = Item(q.get_attribute_value('id'))                                    
            elif i.xml_ns == XMPP_CLIENT_NS and i.xml_name == 'error':
                node.error = Error.from_element(i)

        return node
        
    @staticmethod
    def to_request_item(e):
        iq = Entity.to_element(e)
        pubsub = E(u'pubsub', namespace=XMPP_PUBSUB_NS, parent=iq)
        attrs = {u'node': e.node_name}
        items = E(u'items', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=pubsub)
        if e.item:
            attrs = {u'id': e.item.id}
            E(u'item', attributes=attrs, namespace=XMPP_PUBSUB_NS, parent=items)
            
        if e.subid:
            headers = E(u'headers', namespace=XMPP_SHIM_NS, parent=iq)
            E(u'header', namespace=XMPP_SHIM_NS, parent=headers,
              attributes={u'name': u'pubsub#subid'}, content=e.subid)
        
        print iq.xml()
        return iq

    @staticmethod
    def from_request_item(e):
        node = Node(JID.parse(e.get_attribute_value('from')),
                    JID.parse(e.get_attribute_value('to')),
                    type=e.get_attribute_value('type'),
                    stanza_id=e.get_attribute_value('id'))

        for i in e.xml_children:
            if i.xml_ns in [XMPP_PUBSUB_NS]:
                for p in i.xml_children:
                    if p.xml_ns in [XMPP_PUBSUB_NS]:
                        if p.xml_name == 'items':
                            node.node_name = p.get_attribute_value('node')
                            for q in p.xml_children:
                                if q.xml_name == 'item':
                                    payload = None
                                    if q.xml_children: payload = q.xml_children
                                    node.item = Item(q.get_attribute_value('id'),
                                                     payload=payload)                                    
            elif i.xml_ns == XMPP_CLIENT_NS and i.xml_name == 'error':
                node.error = Error.from_element(i)

        return node
    
    from_request_all_items = from_request_item
    to_request_all_items = to_request_item

