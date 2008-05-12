#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.api.iq import Iq
from headstock.api.stanza import Stanza
from headstock.lib.utils import generate_unique
from bridge.common import XMPP_STANZA_ERROR_NS, XMPP_SASL_NS, XMPP_IBR_NS

__all__ = ['Error']

class Error(object):
    def __init__(self, type, condition, code=None,
                 text=None, lang=None, foreign=None):
        self.type = type
        self.condition = condition.replace('_', '-')
        self.code = code
        self.text = text
        self.lang = lang
        self.foreign = foreign

    def __repr__(self):
        return '<Error %s (%s) at %s>' % (self.condition, self.type or self.code or 'N/A', hex(id(self)))

    @staticmethod
    def from_element(e):
        error_type = e.get_attribute('type')
        code = e.get_attribute('code')
        condition = text = lang = foreign = None
        for child in e.xml_children:
            if child.xml_ns in [XMPP_STANZA_ERROR_NS, XMPP_SASL_NS]:
                if child.xml_name == u'text':
                    text = child.xml_text
                    lang = child.get_attribute('lang')
                else:
                    condition = child.xml_name
            else:
                foreign = child.clone()

        return Error(error_type, condition, code,
                     text, lang, foreign)
        
