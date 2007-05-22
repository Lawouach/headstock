#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.sax.saxutils import escape
from headstock.protocol.core import Entity
from headstock.protocol.core.stanza import Stanza
from headstock.api.im import Body, Subject, Thread

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XML_NS, XML_PREFIX, \
     XMPP_XHTML_IM_NS, XHTML1_NS

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
        
    def unregister_on_chat_with(self, jid):
        self.proxy_registry.cleanup('message.chat.%s' % jid)
    
    ############################################
    # Class methods
    ############################################
    def create_message(cls, from_jid=None, to_jid=None, msg_type=None,
                       bodies=None, subjects=None, threads=None, id=None):
        msg = E(u'message', namespace=XMPP_CLIENT_NS)

        if msg_type:
            A(u'type', value=msg_type, parent=msg)
        
        if from_jid:
            A(u'from', value=from_jid, parent=msg)
        if to_jid:
            A(u'to', value=to_jid, parent=msg)
        if id:
            A(u'id', value=id, parent=msg)
            
        if bodies is None:
            bodies = []
            
        if isinstance(bodies, Body):
            bodies = [body]
            
        for body in bodies:
            plain_body = E(u'body', content=escape(body.plain_body),
                           namespace=XMPP_CLIENT_NS, parent=msg)
            if body.lang:
                A(u'lang', value=body.lang, prefix=XML_PREFIX,
                  namespace=XML_NS, parent=plain_body)
            if body.as_xhtml:
                xhtml_im = E(u'html', namespace=XMPP_XHTML_IM_NS, parent=msg)
                xhtml_body = E(u'body', namespace=XHTML1_NS, parent=xhtml_im)
                if body.lang:
                    A(u'lang', value=body.lang, prefix=XML_PREFIX,
                      namespace=XML_NS, parent=xhtml_body)
                body.xhtml_body.xml_parent = xhtml_body
                xhtml_body.xml_children.append(body.xhtml_body)

        if subjects is None:
            subjects = []

        if isinstance(subjects, Subject):
            subjects = [subjects]

        for subject in subjects:
            sub = E(u'subject', content=subject.body,
                    namespace=XMPP_CLIENT_NS, parent=msg)
            if subject.lang:
                A(u'lang', value=subject.lang, prefix=XML_PREFIX,
                  namespace=XML_NS, parent=sub)

        if threads is None:
            threads = []

        if isinstance(threads, Thread):
            threads = [threads]

        for thread in threads:
            E(u'thread', content=thread.text,
              namespace=XMPP_CLIENT_NS, parent=msg)

        return msg
    create_message = classmethod(create_message) 
    
