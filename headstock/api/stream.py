# -*- coding: utf-8 -*-

from headstock.api import Entity
from bridge.common import XMPP_SASL_NS, XMPP_TLS_NS, XMPP_IBR_NS
from bridge import Element as E

__all__ = ['StreamFeatures']

class StreamFeatures(object):
    def __init__(self):
        self.mechanisms = []
        self.tls = False
        self.register = False

    @staticmethod
    def from_element(e):
        feat = StreamFeatures()
        
        mech = e.get_child('mechanisms', XMPP_SASL_NS)
        if mech:
            for m in mech.xml_children:
                feat.mechanisms.append(m.xml_text)

        feat.register = e.has_child('register', u'http://jabber.org/features/iq-register')
        feat.tls = e.has_child('starttls', XMPP_TLS_NS)

        return feat
