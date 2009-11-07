# -*- coding: utf-8 -*-

from headstock import xmpphandler
from headstock.lib.stanza import Stanza
from headstock.lib.utils import generate_unique
from headstock.error import HeadstockStreamError

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_IBR_NS, XMPP_STANZA_ERROR_NS

__all__ = ['Register']

class Register(object):
    """
    Default class to register a user.
    This will perform the actual register exchange.
    """
    def __init__(self, client, username, password, email=None):
        self.username = username
        self.password = password
        self.email = email
        self.client = client

    @xmpphandler('register', "http://jabber.org/features/iq-register", forget=False)
    def register(self, e):
        iq = Stanza.get_iq(stanza_id=generate_unique())
        E(u'register', namespace=XMPP_IBR_NS, parent=iq)
        return iq
        
    @xmpphandler('query', XMPP_IBR_NS, once=True)
    def handle_registration(self, e):
        iq = Stanza.set_iq(stanza_id=e.xml_parent.get_attribute_value('id'))
        query = E(u'query', namespace=XMPP_IBR_NS, parent=iq)
        E(u'username', content=self.username, namespace=XMPP_IBR_NS, parent=query)
        E(u'password', content=self.password, namespace=XMPP_IBR_NS, parent=query)
        E(u'email', content=self.email, namespace=XMPP_IBR_NS, parent=query)

        self.client.register_on_iq(self.handle_register_success, type=u'result',
                                   id=e.xml_parent.get_attribute_value('id'), once=True)
        
        return iq

    
    def handle_register_success(self, e):
        pass

    @xmpphandler('conflict', XMPP_STANZA_ERROR_NS)
    def handle_register_conflict(self, e):
        pass

    @xmpphandler('resource-constraint', XMPP_STANZA_ERROR_NS)
    def handle_resource_constraint(self, e):
        raise HeadstockStreamError()
