#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.core.stanza import Stanza

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS

__all__ = ['Iq']

class Iq(object):
    #########################################################
    # Class members
    #########################################################
    def create_get_iq(self, from_jid=None, to_jid=None, stanza_id=None):
        return Stanza(u'iq', from_jid, to_jid, u'get', stanza_id).to_bridge()
    create_get_iq = classmethod(create_get_iq)

    def create_set_iq(self, from_jid=None, to_jid=None, stanza_id=None):
        return Stanza(u'iq', from_jid, to_jid, u'set', stanza_id).to_bridge()
    create_set_iq = classmethod(create_set_iq)

    def create_return_iq(self, from_jid=None, to_jid=None, stanza_id=None):
        return Stanza(u'iq', from_jid, to_jid, u'return', stanza_id).to_bridge()
    create_return_iq = classmethod(create_return_iq)
    
    def create_error_iq(self, from_jid=None, to_jid=None, stanza_id=None):
        return Stanza(u'iq', from_jid, to_jid, u'error', stanza_id).to_bridge()
    create_error_iq = classmethod(create_error_iq)

    
