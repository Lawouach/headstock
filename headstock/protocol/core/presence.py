#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.core import Entity
from headstock.core.stanza import Stanza

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS

__all__ = ['Presence']

class Presence(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)

    ############################################
    # Dispatchers proxying
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('presence', self._proxy_dispatcher,
                                         namespace=XMPP_CLIENT_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('presence', namespace=XMPP_CLIENT_NS)

    def _proxy_dispatcher(self, e):
        key = 'presence'
        presence_type = e.get_attribute(u'type')
        if presence_type:
            key = 'presence.%s' % presence_type
        self.proxy_registry.dispatch(key, self, e)
    
    def register_online(self, handler):
        self.proxy_registry.add_dispatcher('presence', handler)

    def register_unavailable(self, handler):
        self.proxy_registry.add_dispatcher('presence.unavailable', handler)

    def register_subscribe(self, handler):
        self.proxy_registry.add_dispatcher('presence.subscribe', handler)
        
    def register_subscribed(self, handler):
        self.proxy_registry.add_dispatcher('presence.subscribed', handler)

    def register_unsubscribed(self, handler):
        self.proxy_registry.add_dispatcher('presence.unsubscribed', handler)

    ############################################
    # Class methods
    ############################################
    def create_presence(cls, from_jid=None, to_jid=None, presence_type=None,
                        status=None, show=None):
        stanza = Stanza(u'presence', from_jid, to_jid, presence_type).to_bridge()
        if status:
            E(u'status', content=status, namespace=stanza.xml_ns, parent=stanza)
        if show:
            E(u'show', content=show, namespace=stanza.xml_ns, parent=stanza)
        
        return stanza
    create_presence = classmethod(create_presence)

    ############################################
    # Public instance methods
    ############################################
    def allow_subscription(self, jid):
        presence = Presence.create_presence(to_jid=jid, presence_type=u'subscribed')
        self.stream.propagate(element=presence)
        
    def reject_subscription(self, jid):
        presence = Presence.create_presence(to_jid=jid, presence_type=u'unsubscribed')
        self.stream.propagate(element=presence)

    def cancel_subscription(self, jid):
        presence = Presence.create_presence(to_jid=jid, presence_type=u'unsubscribed')
        self.stream.propagate(element=presence)

    def unsubscribe(self, jid):
        presence = Presence.create_presence(to_jid=jid, presence_type=u'unsubscribe')
        self.stream.propagate(element=presence)

    def subscribe(self, jid):
        presence = Presence.create_presence(to_jid=jid, presence_type=u'subscribe')
        self.stream.propagate(element=presence)
