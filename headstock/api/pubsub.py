#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['PubSub', 'Configure', 'Subscription', 'Subscriptions']

from headstock.lib.utils import generate_unique
from headstock.protocol.extension.discovery import Disco
from headstock.protocol.extension.pubsub import Service
from headstock.protocol.core.jid import JID
from headstock.api.dataform import Data, Field
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_PUBSUB_NODE_CONFIG_NS

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

class Subscription(object):
    def __init__(self, jid):
        self.jid = jid
        self.node = None
        self.subid = None
        self.subscription = None
        self.affiliation = None

    def __repr__(self):
        return '<Subscription "%s" (%s) (%s) at %s>' % (self.node, str(self.jid),
                                                        self.affiliation or '', hex(id(self)))

class Subscriptions(object):
    def __init__(self):
        self.subscriptions = []

    def __iter__(self):
        return iter(self.subscriptions)

    def find_by_node(self, node_name):
        for sub in self.subscriptions:
            if sub.node == node_name:
                return sub

    def __repr__(self):
        return '<Subscriptions at %s>' % (hex(id(self)),)

class Items(object):
    def __init__(self, max_items=None, node=None, subid=None):
        self.max_items = max_items
        self.node = node
        self.subid = subid
        self.items = []
        
    def __repr__(self):
        return '<Items "%s" on (%s) at %s>' % (self.subid or '', self.node, hex(id(self)),)
    
class Item(object):
    def __init__(self, id=None, payload=None):
        self.id = id
        self.payload = payload

    def __repr__(self):
        return '<Item "%s" at %s>' % (self.id or '', hex(id(self)),)
    
class PubSub(object):
    def __init__(self, session):
        self.session = session
        self.subscriptions_dispatcher = None

    def on_subscriptions_update(self, handler):
        self.subscriptions_dispatcher = handler

    def ask_subscriptions(self, to_jid, node_name=None):
        from_jid = unicode(self.session.stream.jid)
        iq = Service.create_subscriptions(from_jid=from_jid, to_jid=to_jid,
                                          stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def subscriptions_received(self, service, e):
        if not callable(self.subscriptions_dispatcher):
            return
        
        subscriptions = e.get_child('subscriptions', e.xml_ns)
        subscriptions = subscriptions.get_children('subscription', e.xml_ns)
        subs = Subscriptions()
        for subscription in subscriptions:
            sub = Subscription(JID.parse(unicode(subscription.get_attribute('jid'))))
            node = subscription.get_attribute('node')
            if node: sub.node = unicode(node)
            
            subid = subscription.get_attribute('subid')
            if subid: sub.subid = unicode(subid)
            
            affiliation = subscription.get_attribute('affiliation')
            if affiliation: sub.affiliation = unicode(affiliation)
            
            subscription = subscription.get_attribute('subscription')
            if subscription: sub.subscription = unicode(subscription)
            
            subs.subscriptions.append(sub)

        self.subscriptions_dispatcher(subs)
                               
    def ask_affiliations(self, to_jid, node_name=None):
        from_jid = unicode(self.session.stream.jid)
        iq = Service.create_affiliations(from_jid=from_jid, to_jid=to_jid,
                                         stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)
        
    def subscribe(self, to_jid, node_name, jid=None):
        if not jid:
            jid = self.session.stream.jid.nodeid()

        from_jid = unicode(self.session.stream.jid)
        iq = Service.create_subscribe(from_jid, to_jid, jid, node_name)
        self.session.stream.propagate(element=iq)

    def check_configure_support(self, to_jid, node_name):
        iq = Service.create_configure(unicode(self.session.stream.jid),
                                      to_jid, node_name,
                                        stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)
        
    def create_node(self, to_jid, node_name):
        iq = Service.create_create_node(unicode(self.session.stream.jid),
                                        to_jid, node_name,
                                        stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def create_node_whitelist(self, to_jid, node_name):
        c = Configure.create_leaf_node_whitelist()
        iq = Service.create_create_node(unicode(self.session.stream.jid),
                                        to_jid, node_name, c,
                                        stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def delete_node(self, to_jid, node_name):
        iq = Service.create_delete_node(unicode(self.session.stream.jid),
                                        to_jid, node_name, 
                                        stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def purge_items(self, to_jid, node_name):
        iq = Service.create_purge_node(unicode(self.session.stream.jid),
                                       to_jid, node_name, 
                                       stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def publish(self, to_jid, node_name, payload=None):
        iq, item = Service.create_publish(unicode(self.session.stream.jid),
                                          to_jid, node_name,
                                          items_id=generate_unique(),
                                          stanza_id=generate_unique())
        if payload:
            payload = payload.xml_root
            item.xml_children.append(payload)
            payload.xml_parent = item
        self.session.stream.propagate(element=iq)
        
        
