# -*- coding: utf-8 -*-
"""
===========
XMPP stream
===========
The XMPP stream handling in headstock is performed by the
`Stream` module. This should be considered a private module
instanciated by the main client class.
"""

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XML_NS, XML_PREFIX, XMPP_CLIENT_NS, XMPP_STREAM_NS, XMPP_STREAM_PREFIX,\
     XMPP_SASL_NS, XMPP_SASL_PREFIX, XMPP_AUTH_NS, XMPP_TLS_NS, XMPP_CLIENT_NS, XMPP_IBR_NS, \
     XMPP_BIND_NS, XMPP_SESSION_NS, XMPP_DISCO_ITEMS_NS, XMPP_ROSTER_NS, XMPP_COMPONENT_ACCEPT_NS,\
     XMPP_STANZA_ERROR_NS

from headstock import xmpphandler
from headstock.error import HeadstockStartTLS, HeadstockAuthenticationSuccess, \
     HeadstockSessionBound
from headstock.lib.stanza import Stanza
from headstock.lib.utils import generate_unique
from headstock.lib.jid import JID
from headstock.lib.auth.plain import generate_credential, validate_credentials
from headstock.lib.auth.gaa import perform_authentication
from headstock.lib.auth.digest import challenge_to_dict, compute_digest_response

__all__ = ['Stream']

class Stream(object):
    """
    A client stream is the interface between a remote XMPP service
    and the client. It handles the connection and authentication.
    
    ``jid`` :class:`headstock.protocol.core.jid.JID` instance

    ``password`` account's password

    ``tls`` False - flag indicating if the stream runs over a TLS connection

    ``register`` False - flag indicating if the registration was
    requested.
    """
    def __init__(self, jid, password, tls=False, register=False):
        self.jid = jid
        self.password = password

        self.register = register
        self.use_tls = tls

    def stream_header(self):
        """
        Creates and returns a stream header string
        """
        return '<stream:stream xmlns:stream="%s" xmlns="jabber:client" version="1.0" to="%s">' % (XMPP_STREAM_NS,
                                                                                                  self.jid.domain)

    def terminate(self):
        """
        Creates and returns the closing tag of the stream along with
        the unavailable presence stanza.
        """
        return '<presence type="unavailable" /></stream:stream>'
        
    @xmpphandler('error', XMPP_STREAM_NS)
    def handle_error(self, e):
        """
        XMPP handler whenever a stream error is returned.

        Raises a :class:`headstock.error.HeadstockStreamError` instance
        which will be trapped by the client.
        """
        raise HeadstockStreamError()
    
    @xmpphandler('features', XMPP_STREAM_NS)
    def handle_features(self, e):
        """
        XMPP handler for stream features.

        It will:

        * return immediatly if the element has no children.
        * initiates the TLS negociation (from the stream point
        of view) if `self.tls` is `True` and the feature has a
        `<starttls /> child.
        * initiates the authentication based on the supported
        mechanisms or abort if none is found.        
        """
        if not e.xml_children:
            return
        
        if self.use_tls and e.has_child('starttls', XMPP_TLS_NS):
            return "<starttls xmlns='%s' />" % XMPP_TLS_NS

        # We don't actually handle registration here
        # but if the register module has been loaded
        # we do not want to interfere by trying to authenticate straight away either
        if self.register and e.has_child('register', "http://jabber.org/features/iq-register"):
            return

        mech = e.get_child('mechanisms', XMPP_SASL_NS)
        mechanisms = []
        if mech:
            mechanisms = []
            for m in mech.xml_children:
                if m.is_mixed_content():
                    mechanisms.append(m.collapse(separator=''))
                else:
                    mechanisms.append(m.xml_text)
        
        mechanism = None

        # Always favour DIGEST-MD5 if supported by receiving entity
        if u'DIGEST-MD5' in mechanisms:
            mechanism = u'DIGEST-MD5'
            token = None
        elif u'PLAIN' in mechanisms:
            mechanism = u'PLAIN'
            email = '%s@%s' % (self.jid.node, self.jid.domain)
            password = self.password
            token = generate_credential(email, self.jid.node, password)
        elif u'X-GOOGLE-TOKEN' in mechanisms:
            mechanism = u'X-GOOGLE-TOKEN'
            password = self.password
            token = perform_authentication(self.jid.node, password)
        elif u'ANONYMOUS' in mechanisms:            
            mechanism = u'ANONYMOUS'
            token = None
        else:
            # We don't support any of the proposed mechanism
            # let's abort the SASL exchange
            return E(u'abort', namespace=XMPP_SASL_NS)

        return E(u'auth', content=token,
                 attributes={u'mechanism': mechanism},
                 namespace=XMPP_SASL_NS)

    def handle_tls(self):
        """
        Resets the stream header.
        """
        self._send_stream_header()

    @xmpphandler('proceed', XMPP_TLS_NS, once=True)
    def proceed_tls(self, e):
        """
        TLS negociation was successful.

        Raises a :class:`headstock.error.HeadstockStartTLS` instance
        handled by the client.
        """
        raise HeadstockStartTLS()

    @xmpphandler('challenge', XMPP_SASL_NS)
    def handle_challenge(self, e):
        """
        Handles the authentication by computing the
        challenge for the provided credentials.
        """
        response_token = None
        params = challenge_to_dict(e.xml_text)
        # Handling 'rspauth' token in DIGEST-MD5
        # See section 2.1.3 of RFC 2831
        if 'rspauth' not in params:
            digest_uri = 'xmpp/%s' % self.jid.domain
            password = self.password
            response_token = compute_digest_response(params, self.jid.node,
                                                     password, digest_uri=digest_uri)
            
        return E(u'response', content=response_token, namespace=XMPP_SASL_NS)

    @xmpphandler('success', XMPP_SASL_NS, once=True)
    def handle_authenticated(self, e):
        """
        Authentication successful

        Raises a :class:`headstock.error.HeadstockAuthenticationSuccess` instance
        handled by the client.
        """
        raise HeadstockAuthenticationSuccess()

    @xmpphandler('bind', XMPP_BIND_NS, once=True)
    def handle_binding(self, e):
        """
        Handle the JID binding request by returning
        the full JID.
        """
        iq = Stanza.set_iq(stanza_id=generate_unique())
        bind = E(u'bind', namespace=XMPP_BIND_NS, parent=iq)
        if self.jid.resource != None:
            E(u'resource', content=self.jid.resource,
              namespace=XMPP_BIND_NS, parent=bind)

        return iq

    @xmpphandler('session', XMPP_SESSION_NS)
    def handle_session(self, e):
        """
        Handles the session elements received by the server.

        If the type of the response is `result` it raises
        :class:`headstock.error.HeadstockAuthenticationSuccess` instance
        handled by the client indicating the session is ready.

        Otherwise returns the session stanza indicating the
        client wishes to start a session.
        """
        if e.xml_parent and e.xml_parent.get_attribute_value('type') == 'result':
            raise HeadstockSessionBound()
        
        iq = Stanza.set_iq(stanza_id=generate_unique())
        E(u'session', namespace=XMPP_SESSION_NS, parent=iq)
        
        return iq

    @xmpphandler('jid', XMPP_BIND_NS, once=True)
    def handle_jid(self, e):
        """
        Parses the bound JID and sets it to the stream.
        """
        self.jid = JID.parse(e.xml_text)
        
    def notify_presence(self):
        """
        Creates and returns a presence stanza as a
        :class:`bridge.Element` instance.
        """
        return Stanza.to_element(Stanza(u'presence'))

    def ask_roster(self):
        """
        Creates and returns the IQ stanza to query the entity's roster.
        """
        iq = Stanza.get_iq(from_jid=unicode(self.jid), stanza_id=generate_unique())
        E(u'query', namespace=XMPP_ROSTER_NS, parent=iq)   

        return iq
