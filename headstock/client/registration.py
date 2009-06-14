# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.api.jid import JID
from headstock.api import Entity
from headstock.api.registration import Registration
from headstock.lib.utils import generate_unique
from headstock.protocol.extension.register import RegisterDispatcher

from bridge.common import XMPP_IBR_NS

__all__ = ['RegistrationComponent', 'make_linkages']

class RegistrationComponent(component):
    Inboxes = {"inbox"   : "headstock.api.registration.Registration",
               "error"   : "headstock.api.registration.Registration",
               "jid"         : "",
               "register": "",
               "unregister": "",
               "control" : "Shutdown the client stream",}
    
    Outboxes = {"outbox" : "headstock.api.registration.Registration",
                "signal" : "Shutdown signal",
                "success": "",
                "log"    : "log"}
    
    def __init__(self):
        super(RegistrationComponent, self).__init__()
        self.registration_id = None
        self.from_jid = None

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                    isinstance(mes, producerFinished):
                    self.send(mes, "signal")
                    break
                
            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')

            if self.dataReady('register'):
                self.username, self.password = self.recv('register')
                r = Registration()
                self.send(r, 'outbox')
                
            if self.dataReady('unregister'):
                self.recv('unregister')
                self.registration_id = generate_unique()
                r = Registration(type=u'set', from_jid=unicode(self.from_jid),
                                 stanza_id=self.registration_id)
                r.remove = True
                self.send(r, 'outbox')

            if self.dataReady("inbox"):
                r = self.recv('inbox')
                if r.registered:
                    self.send("'%s' is already a registered username." % self.username, 'log')
                    self.send(shutdownMicroprocess(), 'signal')
                elif self.registration_id == r.stanza_id:
                    self.send(None, 'success')
                else:
                    if 'username' in r.infos and 'password' in r.infos:
                        self.registration_id = generate_unique()
                        r = Registration(type=u'set', stanza_id=self.registration_id)
                        r.infos[u'username'] = self.username
                        r.infos[u'password'] = self.password
                        self.send(r, 'outbox')
                
            if self.dataReady("error"):
                r = self.recv('error')
                self.send(r.error, 'log')
                self.send(shutdownMicroprocess(), 'signal')
                break

            if not self.anyReady():
                self.pause()
  
            yield 1

def make_linkages():        
    linkages = {("xmpp", "%s.query" % XMPP_IBR_NS): ("registerdisp", "inbox"),
                ("registerdisp", "log"): ('logger', "inbox"),
                ("registerdisp", "xmpp.error"): ("registerhandler", "error"),
                ("registerdisp", "xmpp.result"): ("registerhandler", "inbox"),
                ("registerhandler", "outbox"): ("registerdisp", "forward"),
                ("registerhandler", "signal"): ("client", "control"),
                ("registerhandler", "success"): ("client", "registered"),
                ("client", "askregistration"): ("registerhandler", "register"),
                ("client", "askunregistration"): ("registerhandler", "unregister"),
                ('jidsplit', 'registerjid'): ('registerhandler', 'jid'),
                ("registerdisp", "outbox"): ("xmpp", "forward"),}
    return dict(registerdisp=RegisterDispatcher(),
                registerhandler=RegistrationComponent()), linkages
