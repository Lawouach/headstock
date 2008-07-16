#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Body', 'Event', 'Message', 'Subject', 'Thread']

from xml.sax.saxutils import unescape
from datetime import datetime

from headstock.api import Entity, Foreign
from headstock.api.jid import JID
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XML_NS, XML_PREFIX, XMPP_CLIENT_NS, \
     XMPP_EVENT_NS, XMPP_XOOB_NS, XMPP_XHTML_IM_NS, XHTML1_NS

class Body(object):
    def __init__(self, content, lang=None):
        self.plain_body = content
        self.lang = lang
        
    def __repr__(self):
        return '<Body at %s>' % (hex(id(self)),)

    def __str__(self):
        return str(self.plain_body)

class XHTMLBody(object):
    def __init__(self, inner):
        self.inner = inner
        
    def __repr__(self):
        return '<XHTMLBody at %s>' % (hex(id(self)),)

class Subject(object):
    def __init__(self, content, lang=None):
        self.content = content
        self.lang = lang

    def __repr__(self):
        return '<Subject at %s>' % (hex(id(self)),)

class Thread(object):
    def __init__(self, text):
        self.text = text
    
    def __repr__(self):
        return '<Thread at %s>' % (hex(id(self)),)

class Event(object):
    offline = u"offline"
    composing = u"composing"
    delivered = u"delivered"
    displayed = u"displayed"

class Message(Entity):
    def __init__(self, from_jid, to_jid, type=u'normal', stanza_id=None, lang=None):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id)
        self.lang = lang

        self.bodies = []
        self.subjects = []
        self.event = None
        self.foreign = []
        self.thread = None
        self.timestamp = datetime.now()

    def __repr__(self):
        return '<Message (%s) at %s>' % (self.stanza_id, hex(id(self)),)

    @staticmethod
    def from_element(e):
        message = Message(JID.parse(e.get_attribute_value('from')),
                          JID.parse(e.get_attribute_value('to')),
                          e.get_attribute_value('type'),
                          e.get_attribute_value('id'),
                          e.get_attribute_value('lang'))

        for child in e.xml_children:
            if not isinstance(child, E):
                continue
            
            if child.xml_ns == XMPP_EVENT_NS:
                if child.has_child('offline', XMPP_EVENT_NS):
                    message.event = Event.offline
                if child.has_child('composing', XMPP_EVENT_NS):
                    message.event = Event.composing
                if child.has_child('delivered', XMPP_EVENT_NS):
                    message.event = Event.delivered
                if child.has_child('displayed', XMPP_EVENT_NS):
                    message.event = Event.displayed

            elif child.xml_ns == XMPP_CLIENT_NS:
                if child.xml_name == 'body':
                    lang = child.get_attribute_value('lang')
                    data = child.collapse(separator='')
                    b = Body(unescape(data), lang=lang)
                    message.bodies.append(b)
                elif child.xml_name == 'subject':
                    lang = child.get_attribute_value('lang')
                    data = child.xml_text or ''
                    b = Subject(unescape(data), lang=lang)
                    message.subjects.append(b)
                elif child.xml_name == 'thread':
                    message.thread = child.xml_text
                if child.xml_name == 'html' and child.xml_ns == XMPP_XHTML_IM_N:
                    b = XHTMLBody(child.xml_children.clone())
                    message.bodies.append(b)
                else:
                    message.foreign.append(Foreign(child))
            else:
                message.foreign.append(Foreign(child))
        
        return message

    @staticmethod
    def to_element(m):
        attrs = {}
        if m.from_jid:
            attrs[u'from'] = unicode(m.from_jid)
        if m.to_jid:
            attrs[u'to'] = unicode(m.to_jid)
        if m.type:
            attrs[u'type'] = m.type
        if m.stanza_id:
            attrs[u'id'] = m.stanza_id
        e = E(u'message', attributes=attrs, namespace=XMPP_CLIENT_NS)

        if m.lang:
            A(u'lang', value=m.lang,
              prefix=XML_PREFIX, namespace=XML_NS, parent=e)

        for subject in m.subjects:
            s = E(u'subject', content=subject.content,
                  namespace=XMPP_CLIENT_NS, parent=e)
            if subject.lang:
                A(u'lang', value=subject.lang,
                  prefix=XML_PREFIX, namespace=XML_NS, parent=s)

        for body in m.bodies:
            if isinstance(body, Body):
                b = E(u'body', content=body.plain_body,
                      namespace=XMPP_CLIENT_NS, parent=e)
                if body.lang:
                    A(u'lang', value=body.lang,
                      prefix=XML_PREFIX, namespace=XML_NS, parent=b)
            elif isinstance(body, XHTMLBody):
                h = E(u'html', namespace=XMPP_XHTML_IM_NS, parent=e)
                b = E(u'body', namespace=XHTML1_NS, parent=h)
                body.inner.xml_parent = b
                b.xml_children.append(body.inner)

        if m.thread:
            E(u'thread', content=m.thread,
              namespace=XMPP_CLIENT_NS, parent=e)

        x = E(u'x', namespace=XMPP_EVENT_NS, parent=e)
        if m.event:
            E(m.event, namespace=XMPP_EVENT_NS, parent=x)

        for f in m.foreign:
            e.xml_children.append(f.e)
            
        return e
