# -*- coding: utf-8 -*-

from headstock.api import Entity

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XML_PREFIX

__all__ = ['Stanza']

class Stanza(Entity):
    def __init__(self, kind=None, from_jid=None, to_jid=None,
                 type=None, stanza_id=None, lang=None):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id)
        self.kind = kind
        self.lang = lang
        self.children = []

    def __repr__(self):
        return '<Stanza "%s" type="%s" from="%s" to="%s" id="%s" at %s>' % (self.kind, self.type, self.from_jid,
                                                                            self.to_jid, self.id, hex(id(self)))
        
    @staticmethod
    def to_element(e, parent=None):
        attributes = {}
        if e.type:
            attributes = {u'type': e.type}
        stanza = E(e.kind, attributes=attributes, parent=parent)
        if e.from_jid:
            A(u'from', value=e.from_jid, parent=stanza)
        if e.to_jid:
            A(u'to', value=e.to_jid, parent=stanza)
        if e.stanza_id:
            A(u'id', value=e.stanza_id, parent=stanza)
        if e.lang:
            A(u'lang', value=e.lang, prefix=XML_PREFIX,
              namespace=XML_NS, parent=stanza)

        return stanza
