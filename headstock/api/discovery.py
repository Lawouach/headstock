# -*- coding: utf-8 -*-

from headstock.lib.utils import generate_unique
from headstock.api.jid import JID
from headstock.api import Entity
from headstock.api.dataform import Data
from headstock.api.error import Error

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS, \
     XMPP_OOB_NS, XMPP_SI_NS, XMPP_SI_FILE_TRANSFER_NS, XMPP_BYTESTREAMS_NS,\
     XMPP_DATA_FORM_NS, XMPP_CLIENT_NS, XMPP_STREAM_NS, XMPP_PUBSUB_NS

__all__ = ['FeaturesDiscovery', 'ItemsDiscovery', 'InformationDiscovery',
           'SubscriptionsDiscovery', 'AffiliationsDiscovery']

class Identity(object):
    def __init__(self, name=None, category=None, type=None):
        self.name = name
        self.category = category
        self.type = type

    def __repr__(self):
        return '<Identity %s (%s) at %s>' % (self.type, self.category, hex(id(self)))

class Feature(object):
    def __init__(self, var=None):
        self.var = var
        
    def __repr__(self):
        return '<Feature %s at %s>' % (self.var, hex(id(self)))

class Item(object):
    def __init__(self, jid=None, action=None, name=None, node=None):
        self.jid = jid
        self.action = action
        self.name = name
        self.node = node
        
    def __repr__(self):
        return '<Item %s %s at %s>' % (self.node or '', str(self.name),
                                       hex(id(self)))

class Subscription(object):
    def __init__(self, node, jid, state):
        self.node = node
        self.jid = jid
        self.state = state

    def __repr__(self):
        return '<Subscription %s [%s:%s] at %s>' % (str(self.jid), self.node, 
                                                    self.state, hex(id(self)))

class Affiliation(object):
    def __init__(self, node, affiliation):
        self.node = node
        self.affiliation = affiliation

    def __repr__(self):
        return '<Affiliation %s (%s) at %s>' % (self.node, self.affiliation, hex(id(self)))

class FeaturesDiscovery(Entity):
    def __init__(self, from_jid, to_jid, node_name=None, type=u'get', stanza_id=None):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id)
        self.data_form = None
        self.node_name = node_name
        self.identities = []
        self.features = []
        self.items = []

    def has_feature(self, feature):
        for f in self.features:
            if f.var == feature:
                return True

        return False
    
    @staticmethod
    def to_element(e):
        iq = Entity.to_element(e)
        attrs = {}
        if e.node_name:
            attrs[u'node'] = e.node_name
        E(u'query', namespace=XMPP_DISCO_INFO_NS, parent=iq,
          attributes=attrs)

        return iq

    @staticmethod
    def from_element(e):
        disco = FeaturesDiscovery(JID.parse(e.get_attribute_value('from')),
                                  JID.parse(e.get_attribute_value('to')),
                                  type=e.get_attribute_value('type'),
                                  stanza_id=e.get_attribute_value('id'))

        for c in e.xml_children:
            if not isinstance(c, E):
                continue
            
            if c.xml_ns in [XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS]:
                for i in c.xml_children:
                    if i.xml_ns in [XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS]:
                        if i.xml_name == 'identity':
                            ident = Identity(i.get_attribute_value('name'),
                                             i.get_attribute_value('category'),
                                             i.get_attribute_value('type'))
                            disco.identities.append(ident)
                        elif i.xml_name == 'feature':
                            feat = Feature(i.get_attribute_value('var'))
                            disco.features.append(feat)
                        elif i.xml_name == 'item':
                            jid = JID.parse(unicode(i.get_attribute_value('jid')))
                            item = Item(jid, i.get_attribute_value('action'),
                                        i.get_attribute_value('name'),
                                        i.get_attribute_value('node'))
                            disco.items.append(item)
                    elif i.xml_ns == XMPP_DATA_FORM_NS:
                        disco.data_form = Data.from_element(i)

        return disco

class ItemsDiscovery(Entity):
    def __init__(self, from_jid, to_jid, node_name=None, type=u'get', stanza_id=None):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id)
        self.items = []
        self.node_name = node_name
    
    @staticmethod
    def to_element(e):
        iq = Entity.to_element(e)
        attrs = {u'node': e.node_name}
        E(u'query', namespace=XMPP_DISCO_ITEMS_NS, parent=iq,
          attributes=attrs)

        return iq

    @staticmethod
    def from_element(e):
        disco = ItemsDiscovery(JID.parse(e.get_attribute_value('from')),
                               JID.parse(e.get_attribute_value('to')),
                               type=e.get_attribute_value('type'),
                               stanza_id=e.get_attribute_value('id'))

        for c in e.xml_children:
            if not isinstance(c, E):
                continue

            if c.xml_ns in [XMPP_DISCO_ITEMS_NS]:
                if c.xml_name == 'query':
                    disco.node_name = c.get_attribute_value('node')
                    for i in c.xml_children:
                        if i.xml_name == 'item' and i.xml_ns in [XMPP_DISCO_ITEMS_NS]:
                            jid = JID.parse(unicode(i.get_attribute_value('jid')))
                            item = Item(jid, i.get_attribute_value('action'),
                                        i.get_attribute_value('name'),
                                        disco.node_name)
                            disco.items.append(item)
            elif c.xml_ns == XMPP_CLIENT_NS and c.xml_name == 'error':
                disco.error = Error.from_element(c)

        return disco

class SubscriptionsDiscovery(Entity):
    def __init__(self, from_jid, to_jid, node_name=None, type=u'get', stanza_id=None):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id)
        self.subscriptions  = []
        self.node_name = node_name
    
    @staticmethod
    def to_element(e):
        iq = Entity.to_element(e)
        query = E(u'query', namespace=XMPP_PUBSUB_NS, parent=iq)
        attr = None
        if e.node_name:
            attr = {u'node': e.node_name}
        E('subscriptions', namespace=XMPP_PUBSUB_NS, attributes=attr, parent=query)

        return iq

    @staticmethod
    def from_element(e):
        disco = SubscriptionsDiscovery(JID.parse(e.get_attribute_value('from')),
                                       JID.parse(e.get_attribute_value('to')),
                                       type=e.get_attribute_value('type'),
                                       stanza_id=e.get_attribute_value('id'))

        for c in e.xml_children:
            if not isinstance(c, E):
                continue

            if c.xml_ns == XMPP_PUBSUB_NS and c.xml_name == 'pubsub':
                for p in c.xml_children:                    
                    if not isinstance(p, E):
                        continue
                    if p.xml_ns == XMPP_PUBSUB_NS and p.xml_name == 'subscriptions':
                        for s in p.xml_children:                    
                            if not isinstance(s, E):
                                continue
                            jid = s.get_attribute_value('jid', None)
                            if jid:
                                JID.parse(jid)
                            sub = Subscription(s.get_attribute_value('node'), jid,
                                               s.get_attribute_value('subscription'))
                            disco.subscriptions.append(sub)
            elif c.xml_ns == XMPP_CLIENT_NS and c.xml_name == 'error':
                disco.error = Error.from_element(c)

        return disco

class AffiliationsDiscovery(Entity):
    def __init__(self, from_jid, to_jid, type=u'get', stanza_id=None):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id)
        self.affiliations  = []
    
    @staticmethod
    def to_element(e):
        iq = Entity.to_element(e)
        query = E(u'query', namespace=XMPP_PUBSUB_NS, parent=iq)
        E('affiliations', namespace=XMPP_PUBSUB_NS, parent=query)

        return iq

    @staticmethod
    def from_element(e):
        disco = AffiliationsDiscovery(JID.parse(e.get_attribute_value('from')),
                                       JID.parse(e.get_attribute_value('to')),
                                       type=e.get_attribute_value('type'),
                                       stanza_id=e.get_attribute_value('id'))
        for c in e.xml_children:
            if not isinstance(c, E):
                continue

            if c.xml_ns == XMPP_PUBSUB_NS and c.xml_name == 'pubsub':
                for p in c.xml_children:                    
                    if not isinstance(p, E):
                        continue
                    if p.xml_ns == XMPP_PUBSUB_NS and p.xml_name == 'affiliations':   
                        for s in p.xml_children:                    
                            if not isinstance(s, E):
                                continue
                            aff = Affiliation(s.get_attribute_value('node'),
                                              s.get_attribute_value('affiliation'))
                            disco.affiliations.append(aff)
            elif c.xml_ns == XMPP_CLIENT_NS and c.xml_name == 'error':
                disco.error = Error.from_element(c)

        return disco

class InformationDiscovery(Entity):
    def __init__(self, from_jid, to_jid, node_name=None, type=u'get', stanza_id=None):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id)
        self.node_name = node_name
    
    @staticmethod
    def to_element(e):
        iq = Entity.to_element(e)
        attrs = {u'node': e.node_name}
        E(u'query', namespace=XMPP_DISCO_INFO_NS, parent=iq,
          attributes=attrs)

        return iq

    @staticmethod
    def from_element(e):
        disco = InformationDiscovery(JID.parse(e.get_attribute_value('from')),
                                   JID.parse(e.get_attribute_value('to')),
                                   type=e.get_attribute_value('type'),
                                   stanza_id=e.get_attribute_value('id'))

        return disco
