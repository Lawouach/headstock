#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['VCard', 'Contact', 'Roster', 'RosterServer']

from headstock.api.message import MessageList
from headstock.api.im import IM
from headstock.lib.utils import generate_unique
from headstock.protocol.core.jid import JID
from headstock.protocol.core.iq import Iq
from headstock.protocol.core.presence import Presence
from headstock.protocol.core.roster import Roster
from headstock.protocol.core.message import Message
from headstock.protocol.extension.last import Last
from bridge.common import XMPP_EVENT_NS, XMPP_LAST_NS, \
     XMPP_OOB_NS, XMPP_XOOB_NS, XMPP_VCARD_NS, XMPP_ROSTER_NS
from bridge import Element as E

OFFLINE = 0
ONLINE = 1

class VCard(object):
    def __init__(self):
        self.fn = None
        self.family = None
        self.given = None
        self.middle = None
        self.nickname = None

    def to_element(self, parent=None):
        vc = E(u'vCard', parent=parent)
        if self.fn:
            E(u'FN', content=self.fn, parent=vc)
            
        if self.family or self.given or self.middle:
            n = E(u'N', parent=vc)
            E(u'FAMILY', content=self.family, parent=n)
            E(u'GIVEN', content=self.given, parent=n)
            E(u'MIDDLE', content=self.middle, parent=n)

        if self.nickname:
            E(u'NICKNAME', content=self.nickname, parent=vc)

        vc.update_prefix(None, None, XMPP_VCARD_NS)

        return vc

    def __repr__(self):
        return '<VCard at %s>' % (hex(id(self)))


class Contact(object):
    def __init__(self, session, jid, availability=OFFLINE):
        self.session = session
        self.jid = jid
        self._jid = unicode(self.jid)
        self.name = None
        self.status = None
        self.state = None
        self.availability = availability
        self.subscription = u'none'
        self.language = None
        self.groups = []
        self.im = IM(self)
        self.contacts = []

    @classmethod
    def from_element(cls, session, item):
        jid = item.get_attribute('jid')
        jid = JID.parse(unicode(jid))
        c = Contact(session, jid)

        name = item.get_attribute('name')
        if name:
            c.name = unicode(name)

        subscription = item.get_attribute('subscription')
        if subscription:
            c.subscription = unicode(subscription)

        groups = item.get_children('group', XMPP_ROSTER_NS)
        for group in groups:
            c.groups.append(group.xml_text)

        return c
        
    def __repr__(self):
        return '<Contact %s (%d) at %s>' % (str(self.jid), self.availability, hex(id(self)))

class Roster(object):
    def __init__(self, session):
        self.session = session
        self.contacts = {}
        
class RosterServer(object):
    def __init__(self, session):
        self.session = session
        
    def subscription_requested(self, presence, e):
        contact = Contact(self.session, jid)
        e = Entity.lookup_by_nodeid(self.stream.jid.nodeid())
        c = Contact.lookup_by_entity_and_fulljid(e, contact.jid)
        
        if not c:
            c = Contact()

        c.jid = unicode(contact.jid)
        c.from_state = u'none' 
        c.to_state = u'out'
        c.state = contact.state
        c.entity_id = e.ID
        c.name = contact.name
        c.status = contact.availability
        e.add(c)
        self.session.storage.save(c)
                
        contact.push(stanza_id=presence.stanza.id)
        
