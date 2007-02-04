#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.core.stanza import Stanza
from headstock.core.iq import Iq
from headstock.lib.utils import generate_unique

#####################################################################################
# From RFC 3921
# In XMPP, one's contact list is called a roster, which consists of any number of
# specific roster items, each roster item being identified by a unique JID.
# A user's roster is stored by the user's server on the user's behalf so that
# the user may access roster information from any resource.
#####################################################################################

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_ROSTER_NS

__all__ = ['Roster']

class Roster(object):
    def __init__(self, stream):
        self.stream = stream
        self._dispatchers = {}
        self._register()

    ############################################
    # Dispatchers registry
    ############################################
    def _register(self):
        client = self.stream.get_client()
        handler = client.get_handler()
        handler.register_on_element('query', namespace=XMPP_ROSTER_NS,
                                    dispatcher=self._proxy_dispatcher)

    def _proxy_dispatcher(self, e):
        print e.xml()
    
    ############################################
    # Class methods
    ############################################
    def create_roster(cls, stanza_type=None, stanza_id=None, items=None):
        iq = Stanza(u'iq', stanza_type=stanza_type, stanza_id=stanza_id).to_bridge()
        query = E(u'query', namespace=XMPP_ROSTER_NS, parent=iq)
        if items:
            for item in items:
                item.xml_parent = query
                query.xml_children.append(item)
        return iq
    create_roster = classmethod(create_roster)

    def create_item(cls, jid, name=None, subscription=None, ask=False, groups=None):
        attributes = {u'jid': jid}
        if name:
            attributes[u'name'] = name
        if subscription:
            attributes[u'subscription'] = subscription
        if ask:
            attributes[u'ask'] = u'subscribe'
        item = E(u'item', attributes=attributes, namespace=XMPP_ROSTER_NS)
        for group in groups:
            E(u'group', content=group, namespace=XMPP_ROSTER_NS, parent=item)

        return item
    create_item = classmethod(create_item)

    ############################################
    # Public instance methods
    ############################################
    def retrieve_roster_list(self):
        iq = Iq.create_get_iq(from_jid=unicode(self.stream.jid),
                              stanza_id=generate_unique())
        E(u'query', namespace=XMPP_ROSTER_NS, parent=iq)             

        self.stream.propagate(element=iq)
