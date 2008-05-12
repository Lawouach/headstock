# -*- coding: utf-8 -*-

from headstock.lib.utils import generate_unique
from headstock.protocol.core.jid import JID
from headstock.api.dataform import Data, Field
from headstock.api import Entity
from headstock.api.error import Error
from bridge.common import XMPP_IBR_NS, XMPP_CLIENT_NS, XMPP_DATA_FORM_NS
from bridge import Element as E

__all__ = ['Registration']

class Registration(Entity):
    def __init__(self, from_jid=None, to_jid=None, type=u'get', stanza_id=None):
        Entity.__init__(self, from_jid, to_jid, type, stanza_id)
        self.x = None
        self.registered = False
        self.remove = False
        self.infos = {}

    @staticmethod
    def from_element(e):
        registration = Registration(JID.parse(e.get_attribute_value('from')),
                                    JID.parse(e.get_attribute_value('to')),
                                    type=e.get_attribute_value('type'),
                                    stanza_id=e.get_attribute_value('id'))
        
        error = e.get_child('error', XMPP_CLIENT_NS)
        if error:
            registration.error = Error.from_element(error)

        query = e.get_child('query', XMPP_IBR_NS)

        for c in query.xml_children:
            if not isinstance(c, E):
                continue
            
            if c.xml_ns == XMPP_DATA_FORM_NS:
                registration.x = Date.from_element(c)
            elif c.xml_ns == XMPP_IBR_NS:
                if c.xml_name == 'remove':
                    registration.remove = True
                elif c.xml_name == 'registered':
                    registration.registered = True
                else:
                    registration.infos[c.xml_name] = c.xml_text

        return registration
        

    @staticmethod
    def to_element(e):
        iq = Entity.to_element(e)
        query = E(u'query', namespace=XMPP_IBR_NS, parent=iq)
        
        if e.remove:
            E(u'remove', namespace=XMPP_IBR_NS, parent=query)
        
        if e.registered:
            E(u'registered', namespace=XMPP_IBR_NS, parent=query)

        for info in e.infos:
           E(info, namespace=XMPP_IBR_NS, parent=query,
             content=e.infos[info]) 

        if e.x:
            Data.to_element(x, parent=query)

        return iq
        
