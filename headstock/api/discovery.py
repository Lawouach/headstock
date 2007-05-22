#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['DiscoveryManager' 'Discovery', 'Identity', 'Feature', 'Item']

from headstock.lib.utils import generate_unique
from headstock.protocol.extension.discovery import Disco
from headstock.protocol.core.jid import JID
from headstock.api.dataform import Data
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS, \
     XMPP_OOB_NS, XMPP_SI_NS, XMPP_SI_FILE_TRANSFER_NS, XMPP_BYTESTREAMS_NS,\
     XMPP_DATA_FORM_NS

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
        return '<Item %s at %s>' % (str(self.jid), hex(id(self)))

class Discovery(object):
    def __init__(self):
        self.identities = []
        self.features = []
        self.items = []
        self.data_form = None
    
class DiscoveryManager(object):
    def __init__(self, session):
        self.session = session
        self.retrieve_dispatcher = None
        self.infos_requested_dispatcher = None
        
    def on_retrieved(self, handler):
        self.retrieve_dispatcher = handler

    def on_infos_requested(self, handler):
        self.infos_requested_dispatcher = handler
        
    def discovery_retrieved(self, discovery, e):
        # If no dispatcher is registered to handle
        # an incoming discovery we don't even care...
        if not callable(self.retrieve_dispatcher):
            return

        disco = Discovery()
        for c in e.xml_children:
            if not isinstance(c, E):
                continue
            
            if c.xml_ns in [XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS]:
                if c.xml_name == 'identity':
                    ident = Identity(c.get_attribute('name'),
                                     c.get_attribute('category'),
                                     c.get_attribute('type'))
                    disco.identities.append(ident)
                elif c.xml_name == 'feature':
                    feat = Feature(c.get_attribute('var'))
                    disco.features.append(feat)
                elif c.xml_name == 'item':
                    jid = JID.parse(unicode(c.get_attribute('jid')))
                    item = Item(jid, c.get_attribute('action'),
                                c.get_attribute('name'),
                                c.get_attribute('node'))
                    disco.items.append(item)
            elif c.xml_ns == XMPP_DATA_FORM_NS:
                disco.data_form = Data.from_element(c)
                
        self.retrieve_dispatcher(disco)

    def send_information(self, discovery, to_jid, from_jid=None):
        from_jid = from_jid or unicode(self.session.stream.jid)
        iq = Disco.create_result_info_query(from_jid=from_jid, to_jid=to_jid,
                                            stanza_id=generate_unique())
        query = iq.get_child('query', XMPP_DISCO_INFO_NS)
        for ident in discovery.identities:
            attrs = {u'category': ident.category, u'type': ident.type}
            if ident.name:
                attrs[u'name'] = ident.name
            E(u'identity', attributes=attrs, parent=query,
              namespace=XMPP_DISCO_INFO_NS)

        for feat in discovery.features:
            E(u'feature', attributes={u'var': feat.var}, parent=query,
              namespace=XMPP_DISCO_INFO_NS)

        self.session.stream.propagate(element=iq)

    def ask_information(self, to_jid, node_name=None, from_jid=None):
        from_jid = unicode(self.session.stream.jid)
        iq = Disco.create_info_query(from_jid=from_jid, to_jid=to_jid,
                                     stanza_id=generate_unique(),
                                     node_name=node_name)
        self.session.stream.propagate(element=iq)

    def send_items(self, discovery, to_jid, from_jid=None):
        from_jid = from_jid or unicode(self.session.stream.jid)
        iq = Disco.create_result_item_query(from_jid=from_jid, to_jid=to_jid,
                                            stanza_id=generate_unique())
        
        query = iq.get_child('query', XMPP_DISCO_ITEMS_NS)
        for item in discovery.items:
            attrs = {u'jid': unicode(item.jid)}
            
            if item.name: attrs[u'name'] = item.name
            if item.node: attrs[u'node'] = item.node
            if item.action: attrs[u'action'] = item.action
            
            E(u'item', attributes=attrs, parent=query,
              namespace=XMPP_DISCO_ITEMS_NS)

        self.session.stream.propagate(element=iq)
            
    def ask_items(self, to_jid, node_name=None, from_jid=None):
        from_jid = unicode(self.session.stream.jid)
        iq = Disco.create_item_query(from_jid=from_jid, to_jid=to_jid,
                                     stanza_id=generate_unique(),
                                     node_name=node_name)
        self.session.stream.propagate(element=iq)
        
    def discovery_request(self, disco, e):
        if e.xml_ns == XMPP_DISCO_INFO_NS:
            if callable(self.infos_requested_dispatcher):
                to_jid = e.xml_parent.get_attribute('from')
                self.infos_requested_dispatcher(to_jid)
