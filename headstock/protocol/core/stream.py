#!/usr/bin/env python
# -*- coding: utf-8 -*-

#####################################################################################
# From RFC 3920
# An XML stream is a container for the exchange of XML elements between any two
# entities over a network.
#####################################################################################

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XML_NS, XML_PREFIX, XMPP_CLIENT_NS, XMPP_STREAM_NS, XMPP_STREAM_PREFIX,\
     XMPP_SASL_NS, XMPP_SASL_PREFIX, XMPP_AUTH_NS, XMPP_TLS_NS, XMPP_CLIENT_NS, XMPP_IBR_NS, \
     XMPP_BIND_NS, XMPP_SESSION_NS, XMPP_DISCO_ITEMS_NS, XMPP_ROSTER_NS, xmpp_bind_as_attr
from bridge.common import ANY_NAMESPACE

from headstock.api.iq import Iq
from headstock.api.stanza import Stanza
from headstock.api.jid import JID

from headstock.lib.auth.plain import generate_credential, validate_credentials
from headstock.lib.auth.gaa import perform_authentication
from headstock.lib.auth.digest import challenge_to_dict, compute_digest_response
from headstock.lib.utils import generate_unique
from headstock.api.stream import StreamFeatures

__all__ = ['ClientStream', 'StreamError', 'SaslError']

# Each one implies the preceding one to have been realized
DISCONNECTED = 0
CONNECTED = 1
AUTHENTICATED = 2
BOUND = 3 # after binding allowed
ACTIVE = 4 # after session allowed
AVAILABLE = 5 # after initial presence

class StreamError(component):
    Inboxes = {"inbox"   : "bridge.Element instance",
               "control" : "",}
    Outboxes = {"outbox" : "bridge.Element instance",
                "signal" : "Shutdown signal",}
    
    def __init__(self):
        super(StreamError, self).__init__()

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                e = self.recv("inbox")
                no_condition_provided = True
                for child in e.xml_children:
                    if child.xml_name == u'text':
                        continue
                    if child.xml_ns == XMPP_STREAM_NS:
                        # The <error/> element MUST contain a child element corresponding
                        # to one of the defined stanza error conditions defined below;
                        no_condition_provided = False
                        break

                if no_condition_provided:
                    error = E(u'error', namespace=XMPP_STREAM_NS)
                    E(u'bad-format', namespace=XMPP_STREAM_NS, parent=error)
                    self.send(error, "outbox")
                    self.send(producerFinished(), "signal")
                    break

                self.send(e, "outbox")

            if not self.anyReady():
                self.pause()
  
            yield 1

class SaslError(component):
    Inboxes = {"inbox"   : "bridge.Element instance",
               "control" : "",}
    Outboxes = {"outbox" : "bridge.Element instance",
                "signal" : "Shutdown signal",}
    
    def __init__(self):
        super(SaslError, self).__init__()

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                e = self.recv("inbox")
                self.send(e, "outbox")

            if not self.anyReady():
                self.pause()
  
            yield 1
            
class ClientStream(component):
    Inboxes = {"inbox"     : "bridge.Element instance",
               "control"   : "Shutdown the client stream",
               "forward"   : "bridge.Element instance to be sent out to the client",
               "auth"      : "Perform authentication",
               "trackingenabled": "",
               "proceedtls": "",
               "tlssuccess": "",
               "tlsfailure": ""}
    
    Outboxes = {"outbox" : "Any string data to be passed to the client",
                "signal" : "Shutdown signal",
                "reset"  : "Reset the parser state",
                "log"    : "String to be logged",
                "error"  : "bridge.Element instance",
                "streamroot": "bridge root element representing the stream",
                "starttls": "",
                "jid"    : "",
                "features": "",
                "track"   : "Tracks element sent",
                "bound"  : "indicates the client has been successfully bound to an XMPP server",
                "terminated": "Indicates the stream has been terminated by the peer",
                "unhandled"    : "Contains any bridge.Element which namespace was not handled by a dedicated component",
                "%s.presence" % XMPP_CLIENT_NS: "Handles 'presence' element in the %s namespace" % XMPP_CLIENT_NS,
                "%s.query" % XMPP_ROSTER_NS: "Handles 'query' element in the %s namespace" % XMPP_ROSTER_NS,
                "%s.message" % XMPP_CLIENT_NS: "Handles 'message' element in the %s namespace" %XMPP_CLIENT_NS}
   
    def __init__(self, jid=None, password_lookup=None, use_tls=False):
        """
        A client stream is the interface between a remote XMPP service
        and the client. It handles the connection and authentication.

        The ``jid`` parameter is an instance of headstock.protocol.core.jid.JID.

        The ``password_lookup`` is a callable that will take the
        provided ``jid`` and should return a clear text password.        
        """
        super(ClientStream, self).__init__()

        self.jid = jid
        self.password_lookup = password_lookup
        self.use_tls = use_tls
        self.tracking_enabled = False

        self.status = DISCONNECTED
        
    def log(self, data, type="INCOMING"):
        """Drops data into the log box. """
        if isinstance(data, E):
            data = data.xml(omit_declaration=True, indent=False)
        self.send((type, data), "log")

    def track(self, element):
        self.send(element.clone().xml_root, 'track')
        
    def propagate(self, element=None, raw=None):
        """Handy method to put either a bridge.Element instance or a raw byte string
        into the outbox box. If element is passed it will set ``raw`` to a serialized
        representation of the XML fragment it represents, as a byte string."""
        if element:
            if self.tracking_enabled:
                self.track(element)
            raw = element.xml(omit_declaration=True, indent=False)
            element.forget()

        if raw:
            self.log(raw, "OUTGOING")
            self.send(raw, "outbox")

    def _trim_end_tag(self, element, omit_decl=False):
        """The stream element is sent opened. We trim the closing tag
        manually."""
        xmlstr = element.xml(indent=False, omit_declaration=omit_decl).strip()
        if xmlstr[-2:] == '/>':
            return '%s>' % xmlstr[:-2].rstrip()
        
        if element.xml_prefix:
            token = '</%s:%s>' % (element.xml_prefix, element.xml_name)
        else:
            token = '</%s>' % element.xml_name

        pos = 0 - len(token)
        return xmlstr[:pos]

    def _send_stream_header(self, omit_decl=False):
        attributes = {u'to': self.jid.domain, u'version': u'1.0'}
        stream = E(u'stream', attributes=attributes,
                   prefix=XMPP_STREAM_PREFIX, namespace=XMPP_STREAM_NS)

        A(u'xmlns', value=XMPP_CLIENT_NS, parent=stream)

        data = self._trim_end_tag(stream, omit_decl)
        stream.forget()
        self.propagate(raw=data)

    def _handle_features(self, e):
        self.log(e)
        self.status = CONNECTED
        feat = StreamFeatures.from_element(e)
        e.forget()
        if feat.tls and self.use_tls:
            tls = E(u'starttls', namespace=XMPP_TLS_NS)
            self.propagate(element=tls)
        elif feat.mechanisms:
            self.send(feat, 'features')
                
    def _handle_tls(self):
        self._reset_stream_header(omit_decl=True)

    def _proceed_tls(self, e):
        self.log(e)
        e.forget()
        self.send('', 'starttls')

    def _handle_challenge(self, e):
        self.log(e)
        response_token = None
        params = challenge_to_dict(e.xml_text)
        # Handling 'rspauth' token in DIGEST-MD5
        # See section 2.1.3 of RFC 2831
        if 'rspauth' not in params:
            digest_uri = 'xmpp/%s' % self.jid.domain
            password = self.password_lookup(self.jid)
            response_token = compute_digest_response(params, self.jid.node,
                                                     password, digest_uri=digest_uri)
            
        e.forget()
        response = E(u'response', content=response_token, namespace=XMPP_SASL_NS)
        self.propagate(element=response)

    def _handle_auth(self, feat):
        mechanism = None

        # Always favour DIGEST-MD5 if supported by receiving entity
        if u'DIGEST-MD5' in feat.mechanisms:
            mechanism = u'DIGEST-MD5'
            token = None
        elif u'PLAIN' in feat.mechanisms:
            mechanism = u'PLAIN'
            email = '%s@%s' % (self.jid.node, self.jid.domain)
            password = self.password_lookup(self.jid)
            token = generate_credential(email, self.jid.node, password)
        elif u'X-GOOGLE-TOKEN' in feat.mechanisms:
            mechanism = u'X-GOOGLE-TOKEN'
            password = self.password_lookup(self.jid)
            token = perform_authentication(self.jid.node, password)
        elif u'ANONYMOUS' in feat.mechanisms:            
            mechanism = u'ANONYMOUS'
            token = None
        else:
            # We don't support any of the proposed mechanism
            # let's abort the SASL exchange
            auth = E(u'abort', namespace=XMPP_SASL_NS)
            self.propagate(element=auth)
            return

        auth = E(u'auth', content=token,
                 attributes={u'mechanism': mechanism},
                 namespace=XMPP_SASL_NS)
        self.propagate(element=auth)

    def _reset_stream_header(self, omit_decl=False):
        self.send("RESET", "reset")
        self._send_stream_header(omit_decl)

    def _handle_authenticated(self, e):
        self.log(e)
        e.forget()
        self.status = AUTHENTICATED
        self._reset_stream_header()

    def _handle_binding(self, e):
        self.log(e)
        e.xml_parent.forget()
        iq = Iq.create_set_iq(stanza_id=generate_unique())
        bind = E(u'bind', namespace=XMPP_BIND_NS, parent=iq)
        if self.jid.resource != None:
            E(u'resource', content=self.jid.resource,
              namespace=XMPP_BIND_NS, parent=bind)

        self.propagate(element=iq)

    def _handle_session(self, e):
        self.log(e)
        e.xml_parent.forget()
        self.status = BOUND
        iq = Iq.create_set_iq(stanza_id=generate_unique())
        E(u'session', namespace=XMPP_SESSION_NS, parent=iq)
        self.propagate(element=iq)

    def _handle_jid(self, e):
        self.log(e)
        self.jid = JID.parse(e.xml_text)
        e.xml_parent.forget()
        
        self.status = ACTIVE

        self.send(self.jid, 'jid')

        # Sends the initial presence information to the server
        self.propagate(element=Stanza.to_element(Stanza(u'presence')))
        
        # Asks immediatly for the client's roster list
        iq = Iq.create_get_iq(from_jid=unicode(self.jid), stanza_id=generate_unique())
        E(u'query', namespace=XMPP_ROSTER_NS, parent=iq)   
        self.propagate(element=iq)
        
    def main(self):
        # Necessary to give the time to the Logger component
        # (if used) to be initialized as well
        yield 1
        self._send_stream_header()
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady('tlssuccess'):
                self.recv('tlssuccess')
                yield 1
                self._handle_tls()
                yield 1

            if self.dataReady("auth"):
                feat = self.recv('auth')
                self._handle_auth(feat)

            if self.dataReady("trackingenabled"):
                self.tracking_enabled = self.recv('trackingenabled')

            if self.dataReady("forward"):
                # The forward box is used by XMPP components to drop a
                # bridge.Element instance that should be passed onto the
                # the outbox in a serialized format (a byte string).
                data = self.recv("forward")
                self.log(data, "OUTGOING")
                if self.tracking_enabled:
                    self.track(data)
                self.send(data.xml(omit_declaration=True, indent=False), "outbox")
                data.forget()

            if self.dataReady("inbox"):
                e = self.recv("inbox")
                # ACTIVE comes once we have finished:
                # * connection
                # * authentication
                # * resource binding
                # * session initiation
                if self.status < ACTIVE:
                    # OK the if/elif thing is ugly. I know.
                    if (e.xml_ns == XMPP_STREAM_NS) and (e.xml_name == 'features'):
                        self._handle_features(e)
                        self.send(e.xml_root, "streamroot")
                    elif (e.xml_ns == XMPP_TLS_NS) and (e.xml_name == 'proceed'):
                        self._proceed_tls(e)
                        yield 1
                    elif (e.xml_ns == XMPP_SASL_NS) and (e.xml_name == 'challenge'):
                        self._handle_challenge(e)
                    elif (e.xml_ns == XMPP_SASL_NS) and (e.xml_name == 'success'):
                        self._handle_authenticated(e)
                    elif (e.xml_ns == XMPP_BIND_NS) and (e.xml_name == 'bind'):
                        self._handle_binding(e)
                    elif (e.xml_ns == XMPP_SESSION_NS) and (e.xml_name == 'session'):
                        self._handle_session(e)
                    elif (e.xml_ns == XMPP_BIND_NS) and (e.xml_name == 'jid'):
                        self._handle_jid(e)
                        yield 1
                        self.send('', 'bound')
                    elif (e.xml_ns == XMPP_SASL_NS) and (e.xml_name == 'failure'):
                        self.send(e, "error")
                    elif (e.xml_ns == XMPP_IBR_NS) and (e.xml_name == 'query'):
                        self.send(e, "%s.%s" % (e.xml_ns, e.xml_name))
                    else:
                        self.send(e, "unhandled")
                elif (e.xml_ns == XMPP_STREAM_NS) and (e.xml_name == 'error'):
                    self.send(e, "error")
                elif (e.xml_ns == XMPP_SASL_NS) and (e.xml_name == 'failure'):
                    self.send(e, "error")
                elif (e.xml_ns == XMPP_STREAM_NS) and (e.xml_name == 'stream'):
                    self.send("", "terminated")
                else:
                    # Once we are authentified and a session was created with
                    # the server we can dispatch the incoming elements to their
                    # correct boxes.
                    key = "%s.%s" % (e.xml_ns, e.xml_name)
                    if key in self.outboxes:
                        self.send(e, key)
                    else:
                        # This step is only reached when a bridge.Element has not
                        # been handled previously. In that case we drop it in the
                        # 'unhandled' box in case another component wants to track this
                        # unhandled element.
                        self.send(e, "unhandled")
                
                e = None
                        
            if not self.anyReady():
                self.pause()
  
            yield 1
