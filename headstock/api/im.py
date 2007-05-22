#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Body', 'Event', 'Message', 'Subject', 'Thread', 'IM']

from xml.sax.saxutils import unescape
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XML_NS, XML_PREFIX, XMPP_EVENT_NS, XMPP_XOOB_NS
from headstock.protocol import core

class Body(object):
    def __init__(self, content, as_xhtml=False, lang=None):
        self.plain_body = content
        self.xhtml_body = None
        self.lang = lang
        self.as_xhtml = as_xhtml
        
        if as_xhtml:
            self.xhtml_body = E.load(content).xml_root
            self.plain_body = self.xhtml_body.collapse()

class Event(object):
    def __init__(self, id=None, offline=False, composing=False,
                 delivered=False, displayed=False):
        self.id = id
        self.offline = offline
        self.composing = composing
        self.delivered = delivered
        self.displayed = displayed

class Subject(object):
    def __init__(self, content, lang=None):
        self.body = content
        self.lang = lang

class Thread(object):
    def __init__(self, text):
        self.text
    
class Message(object):
    def __init__(self, bodies=None, subjects=None, threads=None, event=None):
        self.bodies = bodies
        self.subjects = subjects
        self.threads = threads
        self.event = event

class IM(object):
    def __init__(self, contact):
        self.contact = contact
        if self.contact:
            self._stream = self.contact.session.stream

        self.message_received = None

    def on_message_received(self, handler):
        self.message_received = handler

    def send(self, msg, msg_type=u'chat'):
        msg = core.message.Message.create_message(to_jid=self.contact._jid,
                                                  from_jid=unicode(self._stream.jid),
                                                  bodies=msg.bodies,
                                                  subjects=subjects, threads=threads,
                                                  msg_type=msg_type)
        if msg.event:
            ev = E(u'x', namespace=XMPP_EVENT_NS, parent=msg)
            if msg.event.delivered:
                E(u'delivered', namespace=XMPP_EVENT_NS, parent=ev)
            if msg.event.composing:
                E(u'composing', namespace=XMPP_EVENT_NS, parent=ev)
                if event.id:
                    E(u'id', content=event.id, namespace=XMPP_EVENT_NS, parent=ev)
            if msg.event.offline:
                E(u'offline', namespace=XMPP_EVENT_NS, parent=ev)
            if msg.event.displayed:
                E(u'displayed', namespace=XMPP_EVENT_NS, parent=ev)
                
        self._stream.propagate(element=msg)

    def chat(self, text, lang=None):
        body = Body(content=text, lang=lang)
        msg = core.message.Message.create_message(from_jid=unicode(self._stream.jid),
                                                  to_jid=self.contact._jid,
                                                  bodies=[body], msg_type=u'chat')
        self._stream.propagate(element=msg)
        
    def chat_received(self, msg, e):
        if not callable(self.message_received):
            return
        
        event = e.get_child('x', XMPP_EVENT_NS)
        plain_bodies = []
        bodies = e.get_children('body', e.xml_ns)
        for body in bodies:
            plain_bodies.append(Body(unescape(body.xml_text)))
            
        self.message_received(self.contact, plain_bodies)
        
    def suggest_resource_at(self, body, url, desc=None):
        # http://www.xmpp.org/extensions/xep-0066.html
        msg = core.message.Message.create_message(from_jid=unicode(self._stream.jid),
                                                  to_jid=self.contact._jid, bodies=[body])
        xoob = E(u'x', namespace=XMPP_XOOB_NS, parent=msg)
        E(u'url', content=url, namespace=XMPP_XOOB_NS, parent=xoob)
        if desc:
            E(u'desc', content=desc, namespace=XMPP_XOOB_NS, parent=xoob)
        self._stream.propagate(element=msg)
        
