#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.core import Entity
from headstock.core.stanza import Stanza

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XML_NS, XML_PREFIX

__all__ = ['Message']

class Message(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)

    ############################################
    # Dispatchers registry
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('message', self._proxy_dispatcher,
                                         namespace=XMPP_CLIENT_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('message', namespace=XMPP_CLIENT_NS)
            
    def _proxy_dispatcher(self, e):
        key = 'message'
        msg_type = e.get_attribute(u'type') or 'normal'
        if msg_type:
            key = 'message.%s' % unicode(msg_type)
        from_jid = e.get_attribute(u'from')
        if from_jid:
            key = '%s.%s' % (key, unicode(from_jid))
        self.proxy_registry.dispatch(key, self, e)

    def register_on_normal(self, handler):
        self.proxy_registry.add_dispatcher('message.normal', handler)
    
    def register_on_chat_with(self, jid, handler):
        self.proxy_registry.add_dispatcher('message.chat.%s' % jid, handler)
    
    ############################################
    # Class methods
    ############################################
    def create_message(cls, from_jid=None, to_jid=None, type=None,
                       body=None, subject=None, thread=None, id=None, lang=None):
        msg = E(u'message', namespace=XMPP_CLIENT_NS)

        A(u'type', value=type or u'normal', parent=msg)
        
        if from_jid:
            A(u'from', value=from_jid, parent=msg)
        if to_jid:
            A(u'to', value=to_jid, parent=msg)
        if id:
            A(u'id', value=id, parent=msg)
        if lang:
            A(u'lang', value=lang, prefix=XML_PREFIX, namespace=XML_NS, parent=msg)
            
        if body and isinstance(body, basestring):
            E(u'body', content=body, namespace=XMPP_CLIENT_NS, parent=msg)
        elif body and isinstance(body, list):
            for chunk in body:
                E(u'body', content=chunk, namespace=XMPP_CLIENT_NS, parent=msg)
                
        if subject and isinstance(subject, basestring):
            E(u'subject', content=subject, namespace=XMPP_CLIENT_NS, parent=msg)
        elif subject and isinstance(subject, list):
            for chunk in subject:
                E(u'subject', content=chunk, namespace=XMPP_CLIENT_NS, parent=msg)
                
        if thread:
            E(u'thread', content=thread, namespace=XMPP_CLIENT_NS, parent=msg)
        return msg
    create_message = classmethod(create_message)
