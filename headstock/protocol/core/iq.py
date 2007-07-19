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
        return Stanza(u'iq', from_jid=from_jid, to_jid=to_jid, type=u'get',
                      id=stanza_id).to_element()
    create_get_iq = classmethod(create_get_iq)

    def create_set_iq(self, from_jid=None, to_jid=None, stanza_id=None):
        return Stanza(u'iq', from_jid=from_jid, to_jid=to_jid,
                      type=u'set', id=stanza_id).to_element()
    create_set_iq = classmethod(create_set_iq)

    def create_result_iq(self, from_jid=None, to_jid=None, stanza_id=None):
        return Stanza(u'iq', from_jid=from_jid, to_jid=to_jid,
                      type=u'result', id=stanza_id).to_element()
    create_result_iq = classmethod(create_result_iq)
    
    def create_error_iq(self, from_jid=None, to_jid=None, stanza_id=None):
        return Stanza(u'iq', from_jid=from_jid, to_jid=to_jid,
                      type=u'error', id=stanza_id).to_element()
    create_error_iq = classmethod(create_error_iq)

    
