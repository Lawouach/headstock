# -*- coding: utf-8 -*-
"""
======================
Register class handler
======================

Basic usage
-----------
To register a new user you can simply create an
instance of the `Register` class.

>>> from headstock.client import AsyncClient
>>> c = AsyncClient(u'user@domain', u'secret', hostname='localhost', port=5222, registerclass=Register)
>>> c.set_log(stdout=True)
>>> c.run()

You will not have much control over the XMPP exchange.

More control over the registration process
------------------------------------------
When you want to react at what happens during the XMPP exchange, you
should subclass the `Register` class and implement::

   handle_register_success(e)
   handle_register_conflict(e)
   handle_resource_constraint(e)

"""

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

    ``client`` :class:`headstock.client.BaseClient` instance

    ``username`` username expected to be registered

    ``password`` chosen password for the account

    ``email`` None - account's email
    """
    def __init__(self, client, username, password, email=None):
        self.username = username
        self.password = password
        self.email = email
        self.client = client

    @xmpphandler('register', "http://jabber.org/features/iq-register", forget=False)
    def register(self, e):
        """
        Handler called when the `<register xmlns="http://jabber.org/features/iq-register" />`
        stanza is received and the client required the registration process.

        Returns a stanza indicating the client is indeed requesting the
        registration process from the server.

        ``e`` :class:`bridge.Element` instance representing the dispatched stanza
        """
        iq = Stanza.get_iq(stanza_id=generate_unique())
        E(u'register', namespace=XMPP_IBR_NS, parent=iq)
        return iq
        
    @xmpphandler('query', XMPP_IBR_NS, once=True)
    def handle_registration(self, e):
        """
        Handler called when the server sends the registration form and returns the
        same form filled with at least the username and password.
        
        ``e`` :class:`bridge.Element` instance representing the dispatched stanza
        """
        iq = Stanza.set_iq(stanza_id=e.xml_parent.get_attribute_value('id'))
        query = E(u'query', namespace=XMPP_IBR_NS, parent=iq)
        E(u'username', content=self.username, namespace=XMPP_IBR_NS, parent=query)
        E(u'password', content=self.password, namespace=XMPP_IBR_NS, parent=query)
        if self.email:
            E(u'email', content=self.email, namespace=XMPP_IBR_NS, parent=query)

        self.client.register_on_iq(self.handle_register_success, type=u'result',
                                   id=e.xml_parent.get_attribute_value('id'), once=True)
        
        return iq

    
    def handle_register_success(self, e):
        """
        Handler called when the server replies a IQ stanza indicating the
        registration succeeded.

        Does nothing by default.
        
        ``e`` :class:`bridge.Element` instance representing the dispatched stanza
        """
        pass

    @xmpphandler('conflict', XMPP_STANZA_ERROR_NS)
    def handle_register_conflict(self, e):
        """
        Called when the username is already used on the server.
        
        Does nothing by default.
        
        ``e`` :class:`bridge.Element` instance representing the dispatched stanza
        """
        pass

    @xmpphandler('resource-constraint', XMPP_STANZA_ERROR_NS)
    def handle_resource_constraint(self, e):
        """
        Called when the server limits the resources it allows
        to this connection.

        Raises a :class:`headstock.error.HeadstockStreamError` instance.
        
        ``e`` :class:`bridge.Element` instance representing the dispatched stanza
        """
        raise HeadstockStreamError()
