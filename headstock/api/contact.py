#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Contact']

from headstock.protocol.core.jid import JID
from headstock.api import Entity, Foreign
from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS

OFFLINE = 0
ONLINE = 1

__all__ = ['Presence', 'Roster', 'Item']

class Presence(Entity):
    def __init__(self, from_jid, to_jid):
        Entity.__init__(self, from_jid, to_jid)
        self.status = None
        self.show = None
        self.priority = 0
        self.subscription = u'none'
        self.foreign = []

    def __repr__(self):
        return '<Presence %s (%s) at %s>' % (str(self.from_jid), self.subscription, hex(id(self)))

    @staticmethod
    def from_element(e):
        p = Presence(JID.parse(e.get_attribute_value('from')),
                     JID.parse(e.get_attribute_value('to')))
        p.subscription = e.get_attribute_value('type', None)

        for child in e.xml_children:
            if child.xml_ns == XMPP_CLIENT_NS:
                if child.xml_name == 'show':
                    p.show = child.xml_text
                elif child.xml_name == 'status':
                    p.status = child.xml_text
                elif child.xml_name == 'priority':
                    p.priority = int(child.xml_text)
            else:
                p.foreign.append(Foreign(child))
                
        return p

    @staticmethod
    def to_element(p):
        attrs = {}
        if p.from_jid:
            attrs[u'from'] = unicode(p.from_jid)
        if p.to_jid:
            attrs[u'to'] = unicode(p.to_jid)
        if p.subscription:
            attrs[u'type'] = p.subscription
        e = E(u'presence', attributes=attrs, namespace=XMPP_CLIENT_NS)

        if p.show:
            E(u'show', content=p.show, namespace=XMPP_CLIENT_NS, parent=e)

        if p.status:
            E(u'status', content=p.status, namespace=XMPP_CLIENT_NS, parent=e)

        if p.priority:
            E(u'show', content=unicode(p.priority),
              namespace=XMPP_CLIENT_NS, parent=e)

        for f in p.foreign:
            e.xml_children.append(f.e)
            
        return e

class Item(object):
    def __init__(self, jid):
        self.jid = jid
        self.name = None
        self.status = None
        self.availability = OFFLINE
        self.subscription = u'none'
        self.language = None
        self.groups = []

    def __repr__(self):
        return '<Item %s (%d) at %s>' % (str(self.jid), self.availability, hex(id(self)))

class Roster(Entity):
    def __init__(self, from_jid, to_jid):
        Entity.__init__(self, from_jid, to_jid)
        self.items = {}

    def __repr__(self):
        return '<Roster %s [%d] at %s>' % (str(self.from_jid), len(self.items), hex(id(self)))

    @staticmethod
    def from_element(e):
        r = Roster(JID.parse(e.xml_parent.get_attribute_value('from')),
                   JID.parse(e.xml_parent.get_attribute_value('to')))
        for child in e.xml_children:
            if child.xml_name == 'item':
                jid = JID.parse(unicode(child.get_attribute('jid')))
                nodeid = jid.nodeid()
                item = Item(jid)
                item.name = child.get_attribute_value('name')
                groups = child.get_children('group', ns=child.xml_ns) or []
                for group in groups:
                    item.groups.append(unicode(group))
                item.subscription = child.get_attribute_value('subscription')
                r.items[nodeid] = item
                
        return r
