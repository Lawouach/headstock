#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
from headstock.protocol.core.jid import JID

__all__ = ['Message']

class Message(object):
    def __init__(self):
        self.sender = None
        self.body = []
        self.subject = []
        self.thread = None
        self.timestamp = datetime.now()

    @staticmethod
    def from_element(e):
        message = Message()

        from_jid = e.get_attribute_value('from')
        message.sender = JID.parse(from_jid)
        
        body = e.get_children('body', e.xml_ns) or []
        for chunk in body:
            message.body.append(unicode(chunk))
            
        subjects = e.get_children('subject', e.xml_ns) or []
        for chunk in subjects:
            message.body.append(unicode(chunk))

        
        return message
