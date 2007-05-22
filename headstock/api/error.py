#!/usr/bin/env python
# -*- coding: utf-8 -*-


from headstock.protocol.core.iq import Iq
from headstock.protocol.core.stanza import Stanza, StanzaError
from headstock.lib.utils import generate_unique
from bridge.common import XMPP_STANZA_ERROR_NS, XMPP_SASL_NS

__all__ = ['ErrorManager']

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

    def on_received(self, handler):
        self.received_dispatcher = handler
        
    def received(self, stanza_error, e):
        if not callable(self.received_dispatcher):
            return
        
        error_type = e.get_attribute('type')
        code = e.get_attribute('code')
        condition = text = lang = foreign = None
        for child in e.xml_children:
            if child.xml_ns in [XMPP_STANZA_ERROR_NS, XMPP_SASL_NS]:
                if child.xml_text == 'text':
                    text = child.xml_text
                    lang = child.get_attribute('lang')
                else:
                    condition = child.xml_name
            else:
                foreign = child.clone()

        error = Error(error_type, condition, code,
                      text, lang, foreign)

        self.received_dispatcher(error)

    def send_as_iq(self, to_jid, error, cause=None):
        iq = Iq.create_error_iq(unicode(self.session.stream.jid),
                                to_jid, stanza_id=generate_unique())

        if cause:
            cause.xml_parent = cause
            iq.xml_children.append(cause)
        StanzaError._create_error(error.condition, error.type, legacy=error.code,
                                  text=error.text, lang=error.lang, parent=iq)
        self.session.stream.propagate(element=iq)

    def send_as_presence(self, to_jid, error, cause=None):
        st = Stanza.create(u'presence', unicode(self.session.stream.jid),
                           to_jid, stanza_type=u'error', stanza_id=generate_unique())

        if cause:
            cause.xml_parent = st
            st.xml_children.append(cause)
        StanzaError._create_error(error.condition, error.type, legacy=error.code,
                                  text=error.text, lang=error.lang, parent=st)
        self.session.stream.propagate(element=iq)

    def send_as_message(self, to_jid, error, cause=None):
        st = Stanza.create(u'message', unicode(self.session.stream.jid),
                           to_jid, stanza_type=u'error', stanza_id=generate_unique())

        if cause:
            cause.xml_parent = st
            st.xml_children.append(cause)
        StanzaError._create_error(error.condition, error.type, legacy=error.code,
                                  text=error.text, lang=error.lang, parent=st)
        self.session.stream.propagate(element=iq)
