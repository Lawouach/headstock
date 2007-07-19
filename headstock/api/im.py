#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Body', 'Event', 'Message', 'Subject', 'Thread', 'IM']

from xml.sax.saxutils import unescape
from headstock.lib.utils import generate_unique
from headstock.protocol.core.iq import Iq
from headstock.protocol.extension.discovery import Disco
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XML_NS, XML_PREFIX, XMPP_EVENT_NS, \
     XMPP_XOOB_NS, XMPP_OFFLINE_NS
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
