# -*- coding: utf-8 -*-

import time, sys, Queue
import logging

from headstock.protocol.core.stream import ServerStream
from headstock.protocol.core.stream import DISCONNECTED, BOUND, AVAILABLE
from headstock.api.session import ServerSession
from headstock.api.error import Error
from headstock.error import HeadstockAuthenticationFailure
from headstock.lib.utils import generate_unique, validate_iq_stanza

from bridge import Element as E
from bridge.common import XMPP_TLS_NS
from bridge.parser import DispatchParser
from headstock.application.entity import Entity

__all__ = ['SessionStreamProvider', 'make_threaded_server']

class SessionStreamProvider(object):
    def __init__(self, handler):
        
        self.handler = handler

        # Stream initialization
        from headstock.protocol.core.stream import ServerStream
        self.stream = ServerStream(handler)
        self.stream.proxy_registry.set_logger(handler.server.logger)
        self.stream.set_node_name(handler.server.get_node_name())
        self.stream.initialize_all()

        # Session initialization
        from headstock.api.session import ServerSession
        self.sess = ServerSession(self.stream)
        self.sess.initialize_dispatchers()
        self.sess.set_storage(handler.server.storage)

        self.register_dispatchers()

    def log(self, message):
        self.handler.server.log(message)

    def get_entity(self):
        return Entity.lookup_by_username(self.stream.username)

    def register_dispatchers(self):
        self.stream.register_pre_binding_dispatchers()
        self.stream.on_authentication_received(self.handle_authentication)
        self.stream.on_validate_authentication(self.validate_authentication)
        self.stream.on_disconnected(self.disconnected)
        self.stream.on_bound(self.bound)
        
        self.sess.registration.on_registration_fields_requested(self.registration_fields)
        self.sess.registration.on_registration_submitted(self.registration_submitted)
        self.sess.contacts.on_subscription_requested(self.subscription_requested)
        self.sess.contacts.on_contacts_requested(self.contacts_requested)
        self.sess.contacts.on_contacts_submitted(self.contacts_submitted)
        self.sess.contacts.on_subscription_allowed(self.subscription_allowed)
        self.sess.contacts.on_vcard_requested(self.vcard_requested)
        self.sess.contacts.on_set_online(self.online)
        self.sess.discovery.on_items_requested(self.disco_items_requested)
        self.sess.discovery.on_infos_requested(self.disco_infos_requested)
                                              
        parser = self.stream.client.get_parser()
        parser.register_on_element('starttls', namespace=XMPP_TLS_NS,
                                   dispatcher=self.handle_tls)

        self.sess.set_transmit_handler(self.transmit)

    def get_initiating_features(self):
        from bridge.common import XMPP_STREAM_NS, XMPP_STREAM_PREFIX, XMPP_TLS_NS, XMPP_SASL_NS

        feat = E(u'features', prefix=XMPP_STREAM_PREFIX, namespace=XMPP_STREAM_NS)
        mech = E(u'mechanisms', namespace=XMPP_SASL_NS, parent=feat)
        E(u'mechanism', content=u'DIGEST-MD5', namespace=XMPP_SASL_NS, parent=mech)
        if self.handler.server.tls_enabled:
            # If Use of TLS needs to be established before a particular
            # authentication mechanism may be used, the receiving entity MUST NOT
            # provide that mechanism in the list of available SASL authentication
            # mechanisms prior to TLS negotiation.
            E(u'mechanism', content=u'PLAIN', namespace=XMPP_SASL_NS, parent=mech)
            E(u'starttls', namespace=XMPP_TLS_NS, parent=feat)
        
        return feat
    
    def get_authentication_features(self):
        from bridge.common import XMPP_STREAM_NS, XMPP_STREAM_PREFIX, XMPP_TLS_NS, XMPP_SASL_NS

        feat = E(u'features', prefix=XMPP_STREAM_PREFIX, namespace=XMPP_STREAM_NS)
        mech = E(u'mechanisms', namespace=XMPP_SASL_NS, parent=feat)
        E(u'mechanism', content=u'DIGEST-MD5', namespace=XMPP_SASL_NS, parent=mech)
        if self.handler.server.tls_enabled:
            # If Use of TLS needs to be established before a particular
            # authentication mechanism may be used, the receiving entity MUST NOT
            # provide that mechanism in the list of available SASL authentication
            # mechanisms prior to TLS negotiation.
            E(u'mechanism', content=u'PLAIN', namespace=XMPP_SASL_NS, parent=mech)
        
        return feat


    def get_binding_features(self):
        from bridge.common import XMPP_STREAM_NS, XMPP_STREAM_PREFIX, \
             XMPP_BIND_NS, XMPP_SESSION_NS, XMPP_SASL_NS

        feat = E(u'features', prefix=XMPP_STREAM_PREFIX, namespace=XMPP_STREAM_NS)
        
        E(u'bind', namespace=XMPP_BIND_NS, parent=feat)
        E(u'session', namespace=XMPP_SESSION_NS, parent=feat)

        return feat

    def handle_tls(self, e):
        self.stream.propagate(element=E(u'proceed', namespace=XMPP_TLS_NS))
        self.handler.start_tls()

    def connecting(self):
        feat = self.get_initiating_features()
        self.stream.send_stream_features(feat)

    def authenticating(self):
        feat = self.get_authentication_features()
        self.stream.send_binding_features(feat)

    def binding(self):
        feat = self.get_binding_features()
        self.stream.send_binding_features(feat)

    def bound(self):
        self.stream.register_post_binding_dispatchers()
        
        e = Entity.lookup_by_username(self.stream.username)
        if e != None:
            e.nodeid = self.stream.jid.nodeid()
            e.status = BOUND
            has_it = False
            for rs in e.Resource():
                if rs.value == self.stream.jid.resource:
                    has_it = True
                    break
            if not has_it:
                r = Resource()
                r.value = self.stream.jid.resource
                r.entity_id = e.ID
                self.storage.save(r)
            self.storage.save(e)

    def disconnected(self):
        e = Entity.lookup_by_username(self.stream.username)
        if e != None:
            self.track_logout(e)
            
    def handle_authentication(self, mechanism, token):
        if mechanism == 'DIGEST-MD5':
            from headstock.lib.auth.digest import generate_challenge
            try:
                self.stream.send_challenge(generate_challenge())
            except HeadstockAuthenticationFailure:
                self.stream.send_authentication_failure()
        elif mechanism == 'PLAIN':
            try:
                from headstock.lib.auth.plain import validate_credentials
                authzid, authcid, password = validate_credentials(token)
            except HeadstockAuthenticationFailure:
                self.stream.send_not_authorized_failure()
            
            self.stream.set_auth(authcid, None)
            self.track_login(self.entity)
        else:
            self.stream.send_invalid_mechanism()

        return True

    def validate_authentication(self, token):
        from headstock.lib.auth.digest import validate_response, compute_rspauth,\
             challenge_to_dict
        try:
            username = challenge_to_dict(token).get('username', None)
            password = self.get_password(username)
            validate_response(token, password)
            self.stream.set_auth(username, None)
            self.track_login(self.get_entity())
            self.stream.send_challenge(compute_rspauth(token, password))
        except HeadstockAuthenticationFailure:
            self.stream.send_not_authorized_failure()

        return True

    def get_password(self, username):
        e = Entity.lookup_by_username(username)
        if e != None:
            return e.password

    def track_login(self, user):
        tr = user.Tracker()
        if tr == None:
            tr = Tracker()
            user.add(tr)
        tr.last_ip = self.handler.client_address[0]
        tr.last_login_timestamp = datetime.now()
        self.storage.save(tr)

    def track_logout(self, user):
        tr = user.Tracker()
        if tr == None:
            tr = Tracker()
            user.add(tr)
        tr.last_logout_timestamp = datetime.now()
        self.storage.save(tr)

        user.status = DISCONNECTED
        self.storage.save(user)

    def subscription_requested(self, stanza, contact):
        contact.push_roster(stanza_id=stanza.id)

    def subscription_allowed(self, stanza):
        pass

    def contacts_requested(self, stanza, contact):
        contacts = []
        contact.send_contacts(contacts, stanza_id=stanza.id)

    def contacts_submitted(self, stanza, contact):
        contact.push_contacts(stanza_id=stanza.id)

    def vcard_requested(self, stanza, jid):
        from headstock.protocol.core.iq import Iq
        iq = Iq.create_result_iq(from_jid=unicode(jid), to_jid=unicode(self.stream.jid),
                                 stanza_id=stanza.id)
        self.stream.propagate(element=iq)

    def disco_items_requested(self, st):
        from headstock.api.discovery import Discovery
        self.sess.discovery.send_items(Discovery(), st.to_jid, stanza_id=st.id)

    def disco_infos_requested(self, st):
        from headstock.api.discovery import Discovery, Feature, Identity
        from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS, \
             XMPP_VERSION_NS
        
        d = Discovery()
        #d.identities.append(Identity(category=u'client', type=u'pc'))
        d.features.append(Feature(var=XMPP_DISCO_INFO_NS))
        d.features.append(Feature(var=XMPP_DISCO_ITEMS_NS))
        d.features.append(Feature(var=XMPP_VERSION_NS))
        self.sess.discovery.send_information(d, to_jid=st.from_jid, stanza_id=st.id)

    def online(stanza, contact):
        pass
    
def make_threaded_server(hostname, port, node_name, provider=SessionStreamProvider):
    from headstock.lib.network.threadedserver import make_server
    return make_server(hostname, port, node_name, provider)
