#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.api.activity import Activity

__all__ = ['ActivityDispatcher']

class ActivityDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(ActivityDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                m = self.recv("forward")
                self.send(Activity.to_element(m), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent 
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Activity.from_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1

