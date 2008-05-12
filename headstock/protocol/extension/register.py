# -*- coding: utf-8 -*-

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_IBR_NS

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.api.registration import Registration

__all__ = ['RegisterDispatcher']

class RegisterDispatcher(component):    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : ""}
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity requests",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error"}
    
    def __init__(self):
       super(RegisterDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                m = self.recv("forward")
                self.send(Registration.to_element(m), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent 
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or u'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Registration.from_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1
