#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.core.stanza import Stanza

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS

__all__ = ['Presence']

class Presence(object):
    def __init__(self, stream):
        self.stream = stream
        self._dispatchers = {}
        self._register()

    ############################################
    # Dispatchers registry
    ############################################
    def _register(self):
        client = self.stream.get_client()
        handler = client.get_handler()
        handler.register_on_element('presence', namespace=XMPP_CLIENT_NS,
                                    dispatcher=self._proxy_dispatcher)

    def _proxy_dispatcher(self, e):
        presence_type = e.get_attribute(u'type')
        if not presence_type:
            self._dispatchers[None](self, e)
        else:
            presence_type = unicode(presence_type)
            if presence_type in self._dispatchers:
                self._dispatchers[presence_type](self, e)
    
    def register_online(self, handler):
        self._dispatchers[None] = handler 

    def register_unavailable(self, handler):
        self._dispatchers['unavailable'] = handler

    def register_subscribe(self, handler):
        self._dispatchers['subscribe'] = handler

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
