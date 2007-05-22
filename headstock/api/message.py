#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
from datetime import datetime
from headstock.protocol.core.jid import JID

__all__ = ['Message', 'MessageList']

class Message(object):
    def __init__(self):
        self.sender = None
        self.body = []
        self.subject = []
        self.timestamp = datetime.now()

    def parse(cls, e):
        message = Message()

        from_jid = e.get_attribute('from')
        if from_jid:
            message.sender = JID.parse(unicode(from_jid))
        
        body = e.get_children('body', e.xml_ns) or []
        for chunk in body:
            message.body.append(unicode(chunk))
            
        subjects = e.get_children('subject', e.xml_ns) or []
        for chunk in subjects:
            message.body.append(unicode(chunk))
            
        return message
    parse = classmethod(parse)

class MessageList(object):
    def __init__(self, contact):
        self.contact = contact
        self.has_locking = False
        self.messages = []

    def enable_locking(self):
        self.has_locking = True
        self.lock = threading.Lock()

    def chat_received(self, message, e):
        message = Message.parse(e)
        try:
            if self.has_locking:
                self.lock.acquire()
            self.messages.append(message)
        finally:
            if self.has_locking:
                self.lock.release()

    def pop(self):
        try:
            if self.has_locking:
                self.lock.acquire()
            if self.messages:
                return self.messages.pop()
        finally:
            if self.has_locking:
                self.lock.release()

    def __iter__(self):
        return self.messages
