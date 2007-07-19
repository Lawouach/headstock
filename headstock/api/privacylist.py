#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO: Finish implementation
__all__ = ['PrivacyListManager', 'PrivacyListItem']

from headstock.lib.utils import generate_unique
from headstock.protocol.core.jid import JID
from headstock.protocol.core.iq import Iq
from headstock.protocol.core.privacylist import PrivacyList
from bridge.common import XMPP_PRIVACY_LIST_NS
from bridge import Element as E

class PrivacyListManager(object):
    def __init__(self, session):
        self.session = session
        self.list_not_found_dispatcher = None

    def on_list_not_found(self, handler):
        self.list_not_found_dispatcher = handler

    def ask_available_privacy_lists(self):        
        iq = PrivacyList.retrieve_available_privacy_lists(from_jid=unicode(self.session.stream.jid),
                                                          stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def ask_privacy_list(self, name):        
        iq = PrivacyList.retrieve_privacy_list(from_jid=unicode(self.session.stream.jid),
                                               name=name, stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def list_not_found(self, error, e):
        if callable(self.list_not_found_dispatcher):
            query = e.xml_parent.get_child('query', XMPP_PRIVACY_LIST_NS)
            plist = query.get_child('list', XMPP_PRIVACY_LIST_NS)
            self.list_not_found_dispatcher(unicode(plist.get_attribute('name')))

    def reset_privacy_list(self, name):
        iq = PrivacyList.reset_privacy_list(from_jid=unicode(self.session.stream.jid),
                                            name=name, stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)
