# -*- coding: utf-8 -*-
from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS
from headstock.lib.utils import generate_unique

__all__ = ['Entity', 'Foreign']

class Entity(object):
    def __init__(self, from_jid=None, to_jid=None, type=u'get', stanza_id=None):
        self.from_jid = from_jid
        self.to_jid = to_jid
        self.type = type
        self.stanza_id = stanza_id or generate_unique()
        self.error = None

    @property
    def wasOnError(self):
        return self.error != None

    def swap_jids(self):
        self.from_jid, self.to_jid = self.to_jid, self.from_jid

    @staticmethod
    def to_element(e):
        attrs = {}
        if e.from_jid:
            attrs[u'from'] = unicode(e.from_jid)
        if e.to_jid:
            attrs[u'to'] = unicode(e.to_jid)
        if e.type:
            attrs[u'type'] = e.type
        if e.stanza_id:
            attrs[u'id'] = e.stanza_id
        return E(u'iq', attributes=attrs, namespace=XMPP_CLIENT_NS)

class Foreign(object):
    def __init__(self, e):
        self.e = e

    def __repr__(self):
        return '<Foreign at %s>' % (hex(id(self)),)
