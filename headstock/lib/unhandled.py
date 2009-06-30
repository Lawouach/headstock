# -*- coding: utf-8 -*-
import time

from Axon.AdaptiveCommsComponent import AdaptiveCommsComponent
from Axon.Ipc import shutdownMicroprocess, producerFinished
from Axon.CoordinatingAssistantTracker import coordinatingassistanttracker

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS

__all__ = ['UnhandledComponent', 'make_linkages']

class UnhandledComponent(AdaptiveCommsComponent):
    Inboxes = {"inbox"   : "",
               "temporary": "",
               "control" : "",}
    Outboxes = {"outbox" : "",
                "log"    : "",
                "signal" : "Shutdown signal"}
   
    def __init__(self, service_name, log_unhandled=False):
        super(UnhandledComponent, self).__init__()
        self.service = service_name
        self.log_unhandled = log_unhandled
        
    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")

                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                 stanza = self.recv("inbox")
                 
                 if stanza.xml_name not in ('iq', 'presence', 'message') and\
                         stanza.xml_ns != XMPP_CLIENT_NS:
                     self._log(stanza)
                 else:
                     stanza_id = stanza.get_attribute_value('id')
                     try:
                         linkage = self.retrieveTrackedResourceInformation(stanza_id)
                     except KeyError:
                         self._log(stanza)
                     else:
                         self.send(stanza, stanza_id)
                         self.unlink(thelinkage=linkage)
                         self.ceaseTrackingResource(stanza_id)

            if self.dataReady('temporary'):
                cat = coordinatingassistanttracker.getcat()
                (client, inboxname) = cat.retrieveService(self.service)

                dispatcher, box, stanza_id = self.recv("temporary")
                dispatcher = client.get_component(dispatcher)

                out = self.addOutbox(stanza_id)
                linkage = self.link((self, out), (dispatcher, box))
                self.trackResourceInformation(stanza_id, [], [out], linkage)

            if not self.anyReady():
                self.pause()
  
            yield 1
            
        self.cleanup()

    def _log(self, stanza):
        if self.log_unhandled:
            self.send(('BYPASSED', stanza.xml(omit_declaration=True, indent=False)), 'log')

    def cleanup(self):
        pass

def make_linkages(service_name, log_unhandled=False):
    linkages = {("unhandledhandler", "log"): ('logger', "inbox"),
                ("xmpp", "unhandled"): ("unhandledhandler", "inbox")}
    return dict(unhandledhandler=UnhandledComponent(service_name, log_unhandled)), linkages
    
