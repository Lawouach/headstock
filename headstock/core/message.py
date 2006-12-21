#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.core.stanza import Stanza

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS

__all__ = ['Message']

class Message(Stanza):
    def __init__(self, body, subject=None, from_jid=None, to_jid=None, stanza_id=None):
        Stanza.__init__(self, u'message', from_jid, to_jid, u'chat', stanza_id)

        self.body = body

    def to_bridge(self, parent=None):
        stanza = Stanza.to_bridge(self)
        E(u'body', content=self.body, namespace=stanza.xml_ns, parent=stanza)

        return stanza
        
        
