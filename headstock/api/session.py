#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.api.contact import ContactList
from headstock.api.discovery import DiscoveryManager
from headstock.api.si import FileTransferManager
from headstock.api.version import VersionManager
from headstock.api.error import ErrorManager
from headstock.api.pubsub import PubSub

class Session(object):
    def __init__(self, stream):
        self.stream = stream
        self.jid = None
        self.error = ErrorManager(self)
        self.contacts = ContactList(self)
        self.discovery = DiscoveryManager(self)
        self.files = FileTransferManager(self)
        self.version = VersionManager(self)
        self.pubsub = PubSub(self)

    def initialize_dispatchers(self):
        error = self.stream.stanza_error
        error.register_default_dispatcher(self.error.received)
                                             
        error = self.stream.stream_error
        error.register_default_dispatcher(self.error.received)

        error = self.stream.sasl_error
        error.register_default_dispatcher(self.error.received)
        
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
        roster.register_on_vcard_request(self.contacts.vcard_requested)

        disco = self.stream.discovery
        disco.register_on_list(self.discovery.discovery_retrieved)
        disco.register_on_get(self.discovery.discovery_request)

        si = self.stream.si
        si.register_on_file_transfer(self.files.requested)

        version = self.stream.version
        version.register_requested(self.version.requested)
        version.register_received(self.version.received)

        pubsub = self.stream.pubsub
        pubsub.register_on_received_subscriptions(self.pubsub.subscriptions_received)
        
    def offline(self):
        presence = self.stream.presence.offline(self.jid)
        self.stream.propagate(element=presence)
        
    def online(self):
        presence = self.stream.presence.online(self.jid)
        self.stream.propagate(element=presence)
        
