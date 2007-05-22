#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.core.iq import Iq
from headstock.lib.utils import generate_unique
from headstock.protocol.core import Entity
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_VERSION_NS

__all__ = ['Version']

#####################################################################################
# Defined in XEP-0092
#####################################################################################
class Version(Entity):
    def __init__(self, stream, proxy_registry=None):
        Entity.__init__(self, stream, proxy_registry)

    ############################################
    # Dispatchers registry
    ############################################
    def initialize_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.register('query', self._proxy_dispatcher,
                                         namespace=XMPP_VERSION_NS)

    def cleanup_dispatchers(self):
        if self.proxy_registry:
            self.proxy_registry.cleanup('query', namespace=XMPP_VERSION_NS)
            
    def _proxy_dispatcher(self, e):
        if e.has_child('name', XMPP_VERSION_NS) or \
           e.has_child('version', XMPP_VERSION_NS) or \
           e.has_child('os', XMPP_VERSION_NS):
            self.proxy_registry.dispatch('version.received', self, e)
        else:
            self.proxy_registry.dispatch('version.requested', self, e)

    def register_requested(self, handler):
        self.proxy_registry.add_dispatcher('version.requested', handler)
        
    def register_received(self, handler):
        self.proxy_registry.add_dispatcher('version.received', handler)

    ############################################
    # Class API
    ############################################
    def create_version_response(cls, from_jid, to_jid, name, version, os=None, stanza_id=None):
        iq = Iq.create_result_iq(from_jid=from_jid, to_jid=to_jid,
                                 stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_VERSION_NS, parent=iq)
        E(u'name', content=name, namespace=XMPP_VERSION_NS, parent=query)
        E(u'version', content=version, namespace=XMPP_VERSION_NS, parent=query)
        if os:
            E(u'os', content=os, namespace=XMPP_VERSION_NS, parent=query)

        return iq
    create_version_response = classmethod(create_version_response)
    
    def create_version_request(cls, from_jid, to_jid, stanza_id=None):
        iq = Iq.create_get_iq(from_jid=from_jid, to_jid=to_jid,
                              stanza_id=stanza_id)
        query = E(u'query', namespace=XMPP_VERSION_NS, parent=iq)

        return iq
    create_version_request = classmethod(create_version_request)
