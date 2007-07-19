#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.api.contact import Roster, RosterServer
from headstock.api.discovery import DiscoveryManager
from headstock.api.si import FileTransferManager
from headstock.api.version import VersionManager
from headstock.api.error import ErrorManager
from headstock.api.pubsub import PubSub
from headstock.api.registration import Registration
from headstock.api.privacylist import PrivacyListManager
from headstock.api.rpc import Rpc
from headstock.lib.utils import generate_unique
from headstock.protocol.core.iq import Iq

__all__ = ['Session', 'ServerSession']

class Session(object):
    def __init__(self, stream):
        self.stream = stream
        self.storage = None
        
        self.jid = None
        self.error = ErrorManager(self)
        self.contacts = Roster(self)
        self.discovery = DiscoveryManager(self)
        self.files = FileTransferManager(self)
        self.version = VersionManager(self)
        self.pubsub = PubSub(self)
        self.registration = Registration(self)
        self.privacy_list = PrivacyListManager(self)
        self.rpc = Rpc(self)

    def set_storage(self, storage):
        self.storage = storage

    def initialize_dispatchers(self):
        pass
        
class ServerSession(Session):
    def __init__(self, stream):
        Session.__init__(self, stream)
        self.contacts = RosterServer(self)
        self.features = []

    def initialize_dispatchers(self):
        pass
    
    def transmit(self, obj, e):
        if obj.stanza.kind == 'iq':
            # First we check that that Iq stanza is valid in respect
            # of section 9 of RFC 3920
            try:
                validate_iq_stanza(e)
            except HeadstockInvalidStanzaError, exc:
                err = Error(u'modify', u'bad-request', u'400',
                            text=exc.message.decode(ENCODING), foreign=e)
                self.sess.error.send_as_iq(unicode(self.stream.jid), error=err,
                                           stanza_id=obj.stanza.id)
                return
        
        # If the recipient is not connected then we let the
        # sender know about it
        if obj.stanza.to_jid and not self.handler.server.is_bound(obj.stanza.to_jid):
            err = Error(u'wait', u'recipient-unavailable', u'404', foreign=e)
            self.sess.error.send_as_iq(unicode(self.stream.jid), error=err,
                                       stanza_id=obj.stanza.id)
            return

        # If everything was ok we transmit the Iq stanza to the
        # recipient
        self.stream.propagate(element=stanza)

