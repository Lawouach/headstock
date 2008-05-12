# -*- coding: utf-8 -*-

# supports for XEP 0012

__all__ = ['Activity']

from headstock.api import Entity
from headstock.api.jid import JID
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_LAST_NS, XMPP_CLIENT_NS

class Activity(Entity):
    def __init__(self, from_jid, to_jid, type=u'get', 
                 stanza_id=None, seconds=None, message=None):
       Entity.__init__(self, from_jid, to_jid) 
       self.seconds = seconds
       self.message = message
       self.type = type
       self.stanza_id = stanza_id or generate_unique()

    def __repr__(self):
        return '<Activity (%s) at %s>' % (self.stanza_id, hex(id(self)),)
    
    @staticmethod
    def from_element(e):
        activity = Activity(JID.parse(e.get_attribute_value('from')),
                            JID.parse(e.get_attribute_value('to')),
                            e.get_attribute_value('type'),
                            e.get_attribute_value('id'))

        for child in e.xml_children:
            if not isinstance(child, E):
                continue

            if child.xml_ns == XMPP_LAST_NS:
                seconds = child.get_attribute_value('seconds')
                if seconds != None:
                    activity.seconds = long(seconds)
                activity.message = child.xml_text

        return activity

    @staticmethod
    def to_element(a):
        attrs = {}
        if a.from_jid:
            attrs[u'from'] = unicode(a.from_jid)
        if a.to_jid:
            attrs[u'to'] = unicode(a.to_jid)
        if a.type:
            attrs[u'type'] = a.type
        if a.stanza_id:
            attrs[u'id'] = a.stanza_id
        iq = E(u'iq', attributes=attrs, namespace=XMPP_CLIENT_NS)

        attr = {}
        if a.seconds != None:
            attr[u'seconds'] = unicode(a.seconds)
        E(u'query', namespace=XMPP_LAST_NS, parent=iq,
          content=a.message, attributes=attr)

        return iq
