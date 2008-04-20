#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.api.discovery import FeaturesDiscovery, ItemsDiscovery
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished


__all__ = ['FeaturesDiscoveryDispatcher', 'ItemsDiscoveryDispatcher']

class FeaturesDiscoveryDispatcher(component):
    
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
       super(FeaturesDiscoveryDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                m = self.recv("forward")
                self.send(FeaturesDiscovery.to_element(m), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent 
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or u'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(FeaturesDiscovery.from_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1

class ItemsDiscoveryDispatcher(component):
    
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
       super(ItemsDiscoveryDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                m = self.recv("forward")
                self.send(ItemsDiscovery.to_element(m), "outbox")

            if self.dataReady("inbox"):
                handled = False
                e = self.recv("inbox")
                e = e.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or u'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(ItemsDiscovery.from_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1
