#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.api.contact import ContactList

class Session(object):
    def __init__(self, stream):
        self.stream = stream
        self.jid = None
        self.contacts = ContactList(self)

    def initialize_dispatchers(self):
        presence = self.stream.presence
        presence.register_online(self.contacts.online)
        presence.register_unavailable(self.contacts.unavailable)
        presence.register_subscribe(self.contacts.subscription_requested)
        presence.register_subscribed(self.contacts.subscription_allowed)
        presence.register_unsubscribe(self.contacts.unsubscription_requested)
        presence.register_unsubscribed(self.contacts.subscription_cancelled)

        roster = self.stream.roster
        roster.register_on_list(self.contacts.contacts_retrieved)
        roster.register_on_set(self.contacts.contacts_updated)

    def offline(self):
        presence = self.stream.presence.offline(self.jid)
        self.stream.propagate(element=presence)
        
    def online(self):
        presence = self.stream.presence.online(self.jid)
        self.stream.propagate(element=presence)
        
