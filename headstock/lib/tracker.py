# -*- coding: utf-8 -*-
import time

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS

__all__ = ['StanzaTracker', 'make_linkages']

class StanzaTracker(component):
    Inboxes = {"inbox"   : "UNUSED",
               "control" : "Strop tracking",
               "incoming": "Incoming stanzas",
               "outgoing": "Outgoing stanzas"}
    Outboxes = {"outbox" : "Forwarded incoming stanzas",
                "signal" : "Shutdown signal"}
   
    def __init__(self):
        super(StanzaTracker, self).__init__()
        self.started = self.terminated = None
        self.tracked = {'__INDEX': {}}
        
    def main(self):
        yield 1

        self.started = time.time()
        
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")

                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                 self.recv("inbox")

            if self.dataReady("incoming"):
                e = self.recv("incoming")
                self.send(e, 'outbox')
                self.track(e)

            if self.dataReady("outgoing"):
                e = self.recv("outgoing")
                self.track(e)

            if not self.anyReady():
                self.pause()
  
            yield 1

        self.terminated = time.time()

    @property
    def data(self):
        return self.tracked

    def track(self, e):
        stanza_id = e.get_attribute_value('id')
        if not stanza_id:
            return

        stanza_type = e.get_attribute_value('type')

        tracked = self.tracked
        if stanza_id not in tracked:
             tracked[stanza_id] = {'start': time.time(), 'end': None, 
                                   'type_sent': stanza_type, 'type_received': None}
        else:
            tracked[stanza_id]['end'] = time.time()
            tracked[stanza_id]['type_received'] = stanza_type
             

        for c in e.xml_children:
            if isinstance(c, E):
                if c.xml_ns not in tracked['__INDEX']:
                    tracked['__INDEX'][c.xml_ns] = {}
                    
                if c.xml_name not in tracked['__INDEX'][c.xml_ns]:
                    tracked['__INDEX'][c.xml_ns][c.xml_name] = []

                if stanza_id not in tracked['__INDEX'][c.xml_ns][c.xml_name]:
                    tracked['__INDEX'][c.xml_ns][c.xml_name].append(stanza_id)

def make_linkages():
    linkages = {("xmlparser", "outbox"): ("trackerhandler", "incoming"),
                ("trackerhandler", "outbox"): ('xmpp', "inbox"),
                ("xmpp", "track"): ("trackerhandler", "outgoing"),}
    return dict(trackerhandler=StanzaTracker()), linkages
    
