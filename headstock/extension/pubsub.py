#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.core.iq import Iq
from bridge import Element as E
from bridge.common import XMPP_DISCO_INFO_NS

__all__ = ['Disco']

class Disco(object):
    def __init__(self, stream):
        self.stream = stream

    def ask_features(self, jid, node_name):
        iq = Iq.create_get_iq(from_jid=jid, to_jid=node_name, stanza_id=u'bzzz').to_bridge()
        E(u'query', namespace=XMPP_DISCO_INFO_NS, parent=iq)
        r = self.stream.propagate(element=iq)
        print r.xml()

    def ask_nodes(self, jid, node_name):
        iq = Iq.create_get_iq(from_jid=jid, to_jid=node_name, stanza_id=u'bzzz')
        r = self.stream.propagate(iq)
        print r.xml()
        
    def fetch_node_info(self):
        pass

    def fetch_node_metadata(self):
        pass

    def ask_items(self):
        pass

    def ask_affiliations(self):
        pass
    
