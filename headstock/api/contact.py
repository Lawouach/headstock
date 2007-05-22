#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['VCard', 'Contact', 'ContactList']

from headstock.api.message import MessageList
from headstock.api.im import IM
from headstock.lib.utils import generate_unique
from headstock.protocol.core.jid import JID
from headstock.protocol.core.iq import Iq
from headstock.protocol.core.presence import Presence
from headstock.protocol.core.roster import Roster
from headstock.protocol.core.message import Message
from bridge.common import XMPP_EVENT_NS, XMPP_LAST_NS, \
     XMPP_OOB_NS, XMPP_XOOB_NS, XMPP_VCARD_NS
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
        self.availability = availability
        self.subscription = u'none'
        self.language = None
        self.groups = []
        self.im = IM(self)

    def __repr__(self):
        return '<Contact %s (%d) at %s>' % (str(self.jid), self.availability, hex(id(self)))

    def set_jid(self, jid):
        message = self.session.stream.message
        message.unregister_on_chat_with(self._jid)
        self.jid = jid
        self._jid = unicode(self.jid)
        message.register_on_chat_with(self._jid, self.im.chat_received)
  
    def initialize_dispatchers(self):
        message = self.session.stream.message
        message.register_on_chat_with(self._jid, self.im.chat_received)

    def unsubscribe(self):
        item = Roster.create_item(self._jid, self.name, subscription=u'remove',
                                  groups=self.groups)
        roster = Roster.create_roster(u'set', generate_unique(), [item])
        self.session.stream.propagate(element=roster)
        
        presence = self.session.stream.presence.unsubscribe(self._jid)
        self.session.stream.propagate(element=presence)

    def subscribe(self):
        item = Roster.create_item(self._jid, self.name, groups=self.groups)
        roster = Roster.create_set_roster(stanza_id=generate_unique(), items=[item])
        self.session.stream.propagate(element=roster)
        
        presence = self.session.stream.presence.subscribe(self._jid)
        self.session.stream.propagate(element=presence)

    def accept_subscription(self):
        presence = Presence.allow_subscription(self._jid)
        self.session.stream.propagate(element=presence)

    def ask_last_seen(self):
        # http://www.xmpp.org/extensions/xep-0012.html
        iq = Iq.create_get_iq(unicode(self.session.stream.jid),
                              self._jid, stanza_id=generate_unique())
        E(u'query', namespace=XMPP_LAST_NS, parent=iq)
        self.session.stream.propagate(element=iq)

    def send_last_seen(self, seconds=0, message=None):
        # http://www.xmpp.org/extensions/xep-0012.html
        iq = Iq.create_result_iq(unicode(self.session.stream.jid),
                                 self._jid, stanza_id=generate_unique())
        E(u'query', text=message, attributes={u'seconds': unicode(int(seconds))},
          namespace=XMPP_LAST_NS, parent=iq)
        self.session.stream.propagate(element=iq)

    def resource_at(self, url, desc=None):
        iq = Iq.create_set_iq(unicode(self.session.stream.jid),
                              to_jid=self._jid, 
                              stanza_id=generate_unique())
        query = E(u'query', namespace=XMPP_OOB_NS, parent=iq)
        E(u'url', content=url, namespace=XMPP_OOB_NS, parent=query)
        if desc:
            E(u'desc', content=desc, namespace=XMPP_OOB_NS, parent=query)
        self.session.stream.propagate(element=iq)

    def send_vcard(self, vcard):
        iq = Iq.create_result_iq(unicode(self.session.stream.jid),
                                 to_jid=self._jid, 
                                 stanza_id=generate_unique())
        vcard.to_element(parent=iq)
        self.session.stream.propagate(element=iq)

class ContactList(object):
    def __init__(self, session):
        self.session = session
        self.contacts = {}
        self.pending_subscriptions = {}
        self.update_dispatcher = None
        self.pending_contact_dispatcher = None

    def on_update(self, handler):
        self.update_dispatcher = handler

    def on_subscription_requested(self, handler):
        self.pending_contact_dispatcher = handler

    def ask_contacts(self):
        iq = Roster.retrieve_roster_list(from_jid=unicode(self.session.stream.jid),
                                         stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def contacts_retrieved(self, roster, e):
        for child in e.xml_children:
            if child.xml_name == 'item':
                jid = JID.parse(unicode(child.get_attribute('jid')))
                nodeid = jid.nodeid()
                contact = Contact(self.session, jid)
                name = child.get_attribute('name')
                if name:
                    contact.name = name
                contact.initialize_dispatchers()
                groups = child.get_children('group', ns=child.xml_ns) or []
                for group in groups:
                    contact.groups.append(unicode(group))
                subscription = child.get_attribute('subscription')
                if subscription:
                    contact.subscription = unicode(subscription)
                self.contacts[nodeid] = contact
                
        if callable(self.update_dispatcher):
            self.update_dispatcher()

    def contacts_updated(self, roster, e):
        iq = self.session.stream.roster.create_result_roster(stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def online(self, presence, e):
        jid = JID.parse(unicode(e.get_attribute('from')))
        nodeid = jid.nodeid()
        fulljid = unicode(jid)
        if nodeid in self.contacts:
            contact = self.contacts[nodeid]
            contact.set_jid(jid)
            del self.contacts[nodeid]
            self.contacts[fulljid] = contact
        elif fulljid in self.contacts:
            contact = self.contacts[fulljid]
        else:
            contact = Contact(self.session, jid, ONLINE)
            contact.initialize_dispatchers()
            self.contacts[fulljid] = contact
        contact.availability = ONLINE

        status = e.get_children('status', ns=e.xml_ns)
        if status:
            contact.status = unicode(status)

        if callable(self.update_dispatcher):
            self.update_dispatcher()
        
    def unavailable(self, presence, e):
        jid = JID.parse(unicode(e.get_attribute('from')))
        nodeid = jid.nodeid()
        fulljid = unicode(jid)
        if nodeid in self.contacts:
            contact = self.contacts[nodeid]
        elif fulljid in self.contacts:
            contact = self.contacts[fulljid]
        else:
            contact = Contact(self.session, jid)
            contact.initialize_dispatchers()
        contact.availability = OFFLINE
        
        status = e.get_children('status', ns=e.xml_ns)
        if status:
            contact.status = unicode(status)
            
        if callable(self.update_dispatcher):
            self.update_dispatcher()

    def subscription_requested(self, presence, e):
        if not callable(self.pending_contact_dispatcher):
            return

        jid = JID.parse(unicode(e.get_attribute('from')))
        self.pending_contact_dispatcher(Contact(self.session, jid))
        
    def unsubscription_requested(self, presence, e):
        jid = JID.parse(unicode(e.get_attribute('from')))
        nodeid = jid.nodeid()
        contact = None
        if nodeid in self.contacts:
            contact = self.contacts[nodeid]
            del self.contacts[nodeid]
        if nodeid in self.pending_subscriptions:
            del self.pending_subscriptions[nodeid]

        if contact:
            contact.unsubscribe()
        if callable(self.update_dispatcher):
            self.update_dispatcher()
        
    def subscription_allowed(self, presence, e):
        jid = JID.parse(unicode(e.get_attribute('from')))
        nodeid = jid.nodeid()
        contact = Contact(self.session, jid, ONLINE)
        contact.initialize_dispatchers()
        self.contacts[nodeid] = contact
        
    def subscription_cancelled(self, presence, e):
        jid = JID.parse(unicode(e.get_attribute('from')))
        nodeid = jid.nodeid()
        if nodeid in self.contacts:
            contact = self.contacts[nodeid]
            del self.contacts[nodeid]
        if nodeid in self.pending_subscriptions:
            del self.pending_subscriptions[nodeid]

        contact.subscribe()
        
    def vcard_requested(self, roster, e):
        print e.xml()
