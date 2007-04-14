#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Contact', 'ContactList']

from headstock.api.message import MessageList
from headstock.lib.utils import generate_unique
from headstock.protocol.core.jid import JID
from headstock.protocol.core.roster import Roster
from headstock.protocol.core.message import Message

OFFLINE = 0
ONLINE = 1

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
        self.messages = MessageList(self)

    def __repr__(self):
        return '<Contact %s (%d) at %s>' % (str(self.jid), self.availability, hex(id(self)))
  
    def initialize_dispatchers(self):
        message = self.session.stream.message
        message.register_on_chat_with(self._jid, self.messages.chat_received)

    def unsubscribe(self):
        item = Roster.create_item(self._jid, self.name, subscription=u'none',
                                  groups=self.groups)
        roster = Roster.create_roster(u'set', generate_unique(), [item])
        self.session.stream.propagate(element=roster)
        
        presence = self.session.stream.presence.unsubscribe(self._jid)
        self.session.stream.propagate(element=presence)

    def subscribe(self):
        item = Roster.create_item(self._jid, self.name, groups=self.groups)
        roster = Roster.create_roster(u'set', generate_unique(), [item])
        self.session.stream.propagate(element=roster)

    def chat(self, content):
        self.session.stream.message.chat(self._jid, content, self.language)
        
class ContactList(object):
    def __init__(self, session):
        self.session = session
        self.contacts = {}
        self.pending_subscriptions = {}
        self.update_dispatcher = None

    def on_update(self, handler):
        self.update_dispatcher = handler

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
        print self.contacts

    def contacts_updated(self, roster, e):
        iq = self.session.stream.roster.create_roster(u'result', generate_unique())
        self.session.stream.propagate(element=iq)

    def online(self, presence, e):
        jid = JID.parse(unicode(e.get_attribute('from')))
        nodeid = jid.nodeid()
        if nodeid in self.contacts:
            contact = self.contacts[nodeid]
        else:
            contact = Contact(self.session, jid, ONLINE)
            contact.initialize_dispatchers()
            self.contacts[nodeid] = contact
        contact.availability = ONLINE

        status = e.get_children('status', ns=e.xml_ns)
        if status:
            contact.status = unicode(status)
        if callable(self.update_dispatcher):
            self.update_dispatcher()
        print self.contacts
        
    def unavailable(self, presence, e):
        jid = JID.parse(unicode(e.get_attribute('from')))
        nodeid = jid.nodeid()
        if nodeid in self.contacts:
            contact = self.contacts[nodeid]
        else:
            contact = Contact(self.session, jid)
            contact.initialize_dispatchers()
            self.contacts[nodeid] = contact
        contact.availability = OFFLINE
        
        status = e.get_children('status', ns=e.xml_ns)
        if status:
            contact.status = unicode(status)
        if callable(self.update_dispatcher):
            self.update_dispatcher()
        print self.contacts

    def subscription_requested(self, presence, e):
        jid = JID.parse(unicode(e.get_attribute('from')))
        nodeid = jid.nodeid()
        self.pending_subscriptions[nodeid] = Contact(self.session, jid)
    
        #p = self.session.stream.presence.allow_subscription(unicode(jid))
        #self.session.stream.propagate(element=p)
        
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
        print self.contacts
        
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
        print self.contacts
        
