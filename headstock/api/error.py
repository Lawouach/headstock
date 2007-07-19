#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.core.iq import Iq
from headstock.protocol.core.stanza import Stanza, StanzaError
from headstock.lib.utils import generate_unique
from bridge.common import XMPP_STANZA_ERROR_NS, XMPP_SASL_NS, XMPP_IBR_NS


__all__ = ['Error', 'ErrorManager']

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
    
class ErrorManager(object):
    def __init__(self, session):
        self.session = session
        self.received_dispatcher = None
        self.alternate_dispatchers = {}

    def on_received(self, handler):
        self.received_dispatcher = handler

    def register_alternate_dispatcher(self, handler, namespace, code=None, name=None):
        if code:
            key = "%s.%s" % (code, namespace)
            self.alternate_dispatchers[key] = handler
        if name:
            key = "%s.%s" % (name, namespace)
            self.alternate_dispatchers[key] = handler

    def from_element(self, e):
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
        
    def received(self, stanza_error, e):
        if not callable(self.received_dispatcher):
            return

        error = self.from_element(e)
        
        key = None
        iq_parent = e.xml_parent
        for child in iq_parent.xml_children:
            if child.xml_ns != iq_parent.xml_ns:
                code = e.get_attribute('code')
                if code:
                    key = "%s.%s" % (unicode(code), child.xml_ns)
                else:
                    for child in e.xml_children:
                        if child.xml_ns == XMPP_STANZA_ERROR_NS:
                            key = "%s.%s" % (child.xml_name, child.xml_ns)
                            break

                if key and key in self.alternate_dispatchers:
                    self.alternate_dispatchers[key](error, child)
                    return


        self.received_dispatcher(error)

    def send_as_iq(self, to_jid, error, stanza_id=None):
        if not stanza_id:
            stanza_id = generate_unique()
            
        iq = StanzaError.create_as_iq(unicode(self.session.stream.jid), to_jid,
                                      error.condition, error.type, legacy=error.code,
                                      text=error.text, lang=error.lang, stanza_id=stanza_id,
                                      children=[error.foreign])
        self.session.stream.propagate(element=iq)

    def send_as_presence(self, to_jid, error, stanza_id=None):
        if not stanza_id:
            stanza_id = generate_unique()
            
        st = StanzaError.create_as_presence(unicode(self.session.stream.jid),
                                            to_jid, error.condition, error.type, legacy=error.code,
                                            text=error.text, lang=error.lang, stanza_id=stanza_id,
                                            children=[error.foreign])
        self.session.stream.propagate(element=st)

    def send_as_message(self, to_jid, error, stanza_id=None):
        if not stanza_id:
            stanza_id = generate_unique()

        st = StanzaError.create_as_message(unicode(self.session.stream.jid),
                                           to_jid, error.condition, error.type, legacy=error.code,
                                           text=error.text, lang=error.lang, stanza_id=stanza_id,
                                           children=[error.foreign])
        self.session.stream.propagate(element=st)
