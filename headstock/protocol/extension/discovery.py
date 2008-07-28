# -*- coding: utf-8 -*-

from headstock.api.discovery import FeaturesDiscovery, ItemsDiscovery,\
    SubscriptionsDiscovery, AffiliationsDiscovery, InformationDiscovery
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished


__all__ = ['FeaturesDiscoveryDispatcher', 'ItemsDiscoveryDispatcher',
           'SubscriptionsDiscoveryDispatcher', 'AffiliationsDiscoveryDispatcher',
           'InformationDiscoveryDispatcher', 'DiscoveryDispatcher']

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
                "xmpp.set"     : "Activity requests",
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
                "xmpp.set"     : "Activity requests",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(ItemsDiscoveryDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
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

class SubscriptionsDiscoveryDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity requests",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(SubscriptionsDiscoveryDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                m = self.recv("forward")
                self.send(SubscriptionsDiscovery.to_element(m), "outbox")

            if self.dataReady("inbox"):
                handled = False
                s = self.recv("inbox")
                e = s.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or u'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(SubscriptionsDiscovery.from_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1

class AffiliationsDiscoveryDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity requests",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(AffiliationsDiscoveryDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                m = self.recv("forward")
                self.send(AffiliationsDiscovery.to_element(m), "outbox")

            if self.dataReady("inbox"):
                handled = False
                s = self.recv("inbox")
                e = s.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or u'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(AffiliationsDiscovery.from_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1

class InformationDiscoveryDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity requests",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(InformationDiscoveryDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                   isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                m = self.recv("forward")
                self.send(InformationDiscovery.to_element(m), "outbox")

            if self.dataReady("inbox"):
                handled = False
                s = self.recv("inbox")
                e = s.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or u'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(InformationDiscovery.from_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1


class DiscoveryDispatcher(component):
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               
               "features.inbox": "",
               "subscription.inbox": "",
               "affiliation.inbox": "",
               "items.inbox": "",
               "info.inbox": "",
               
               "features.forward": "",
               "subscription.forward": "",
               "affiliation.forward": "",
               "items.forward": "",
               "info.forward": "",
               
               "in.features.get"     : "Activity requests",
               "in.features.set"     : "Activity requests",
               "in.features.result"  : "Activity responses",
               "in.features.error"   : "Activity response error",
               "in.items.get"     : "Activity requests",
               "in.items.set"     : "Activity requests",
               "in.items.result"  : "Activity responses",
               "in.items.error"   : "Activity response error",
               "in.subscription.get"     : "Activity requests",
               "in.subscription.set"     : "Activity requests",
               "in.subscription.result"  : "Activity responses",
               "in.subscription.error"   : "Activity response error",
               "in.affiliation.get"     : "Activity requests",
               "in.affiliation.set"     : "Activity requests",
               "in.affiliation.result"  : "Activity responses",
               "in.affiliation.error"   : "Activity response error",
               "in.info.get"     : "Activity requests",
               "in.info.set"     : "Activity requests",
               "in.info.result"  : "Activity responses",
               "in.info.error"   : "Activity response error",}
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",

                "features.outbox": "",
                "subscription.outbox": "",
                "affiliation.outbox": "",
                "items.outbox": "",
                "info.outbox": "",
                
                "out.features.get"     : "Activity requests",
                "out.features.set"     : "Activity requests",
                "out.features.result"  : "Activity responses",
                "out.features.error"   : "Activity response error",
                "out.items.get"     : "Activity requests",
                "out.items.set"     : "Activity requests",
                "out.items.result"  : "Activity responses",
                "out.items.error"   : "Activity response error",
                "out.subscription.get"     : "Activity requests",
                "out.subscription.set"     : "Activity requests",
                "out.subscription.result"  : "Activity responses",
                "out.subscription.error"   : "Activity response error",
                "out.affiliation.get"     : "Activity requests",
                "out.affiliation.set"     : "Activity requests",
                "out.affiliation.result"  : "Activity responses",
                "out.affiliation.error"   : "Activity response error",
                "out.info.get"     : "Activity requests",
                "out.info.set"     : "Activity requests",
                "out.info.result"  : "Activity responses",
                "out.info.error"   : "Activity response error",
                }
    
    def __init__(self):
        super(DiscoveryDispatcher, self).__init__() 

    def initComponents(self):        
        subdisp = SubscriptionsDiscoveryDispatcher()
        self.link((self, 'subscription.inbox'), (subdisp, 'inbox'), passthrough=1)
        self.link((self, 'subscription.forward'), (subdisp, 'forward'), passthrough=1)
        self.link((self, 'in.subscription.get'), (subdisp, 'forward'), passthrough=1)
        self.link((self, 'in.subscription.set'), (subdisp, 'forward'), passthrough=1)
        self.link((self, 'in.subscription.result'), (subdisp, 'forward'), passthrough=1)
        self.link((self, 'in.subscription.error'), (subdisp, 'forward'), passthrough=1)
        self.link((subdisp, 'outbox'), (self, 'subscription.outbox'), passthrough=2)
        self.link((subdisp, 'xmpp.get'), (self, 'out.subscription.get'), passthrough=2)
        self.link((subdisp, 'xmpp.set'), (self, 'out.subscription.set'), passthrough=2)
        self.link((subdisp, 'xmpp.result'), (self, 'out.subscription.result'), passthrough=2)
        self.link((subdisp, 'xmpp.error'), (self, 'out.subscription.error'), passthrough=2)
        self.link((subdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((subdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(subdisp)
        subdisp.activate()      

        affdisp = AffiliationsDiscoveryDispatcher()
        self.link((self, 'affiliation.inbox'), (affdisp, 'inbox'), passthrough=1)
        self.link((self, 'affiliation.forward'), (affdisp, 'forward'), passthrough=1)
        self.link((self, 'in.affiliation.get'), (affdisp, 'forward'), passthrough=1)
        self.link((self, 'in.affiliation.set'), (affdisp, 'forward'), passthrough=1)
        self.link((self, 'in.affiliation.result'), (affdisp, 'forward'), passthrough=1)
        self.link((self, 'in.affiliation.error'), (affdisp, 'forward'), passthrough=1)
        self.link((affdisp, 'outbox'), (self, 'affiliation.outbox'), passthrough=2)
        self.link((affdisp, 'xmpp.get'), (self, 'out.affiliation.get'), passthrough=2)
        self.link((affdisp, 'xmpp.set'), (self, 'out.affiliation.set'), passthrough=2)
        self.link((affdisp, 'xmpp.result'), (self, 'out.affiliation.result'), passthrough=2)
        self.link((affdisp, 'xmpp.error'), (self, 'out.affiliation.error'), passthrough=2)
        self.link((affdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((affdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(affdisp)
        affdisp.activate()
    
        featdisp = FeaturesDiscoveryDispatcher()
        self.link((self, 'features.inbox'), (featdisp, 'inbox'), passthrough=1)
        self.link((self, 'features.forward'), (featdisp, 'forward'), passthrough=1)
        self.link((self, 'in.features.get'), (featdisp, 'forward'), passthrough=1)
        self.link((self, 'in.features.set'), (featdisp, 'forward'), passthrough=1)
        self.link((self, 'in.features.result'), (featdisp, 'forward'), passthrough=1)
        self.link((self, 'in.features.error'), (featdisp, 'forward'), passthrough=1)
        self.link((featdisp, 'outbox'), (self, 'outbox'), passthrough=2)
        self.link((featdisp, 'xmpp.get'), (self, 'out.features.get'), passthrough=2)
        self.link((featdisp, 'xmpp.set'), (self, 'out.features.set'), passthrough=2)
        self.link((featdisp, 'xmpp.result'), (self, 'out.features.result'), passthrough=2)
        self.link((featdisp, 'xmpp.error'), (self, 'out.features.error'), passthrough=2)
        self.link((featdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((featdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(featdisp)
        featdisp.activate()

        itemsdisp = ItemsDiscoveryDispatcher()
        self.link((self, 'items.inbox'), (itemsdisp, 'inbox'), passthrough=1)
        self.link((self, 'items.forward'), (itemsdisp, 'forward'), passthrough=1)
        self.link((self, 'in.items.get'), (itemsdisp, 'forward'), passthrough=1)
        self.link((self, 'in.items.set'), (itemsdisp, 'forward'), passthrough=1)
        self.link((self, 'in.items.result'), (itemsdisp, 'forward'), passthrough=1)
        self.link((self, 'in.items.error'), (itemsdisp, 'forward'), passthrough=1)
        self.link((itemsdisp, 'outbox'), (self, 'outbox'), passthrough=2)
        self.link((itemsdisp, 'xmpp.get'), (self, 'out.items.get'), passthrough=2)
        self.link((itemsdisp, 'xmpp.set'), (self, 'out.items.set'), passthrough=2)
        self.link((itemsdisp, 'xmpp.result'), (self, 'out.items.result'), passthrough=2)
        self.link((itemsdisp, 'xmpp.error'), (self, 'out.items.error'), passthrough=2)
        self.link((itemsdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((itemsdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(itemsdisp)
        itemsdisp.activate()

        infodisp = InformationDiscoveryDispatcher()
        self.link((self, 'info.inbox'), (infodisp, 'inbox'), passthrough=1)
        self.link((self, 'info.forward'), (infodisp, 'forward'), passthrough=1)
        self.link((self, 'in.info.get'), (infodisp, 'forward'), passthrough=1)
        self.link((self, 'in.info.set'), (infodisp, 'forward'), passthrough=1)
        self.link((self, 'in.info.result'), (infodisp, 'forward'), passthrough=1)
        self.link((self, 'in.info.error'), (infodisp, 'forward'), passthrough=1)
        self.link((infodisp, 'outbox'), (self, 'outbox'), passthrough=2)
        self.link((infodisp, 'xmpp.get'), (self, 'out.info.get'), passthrough=2)
        self.link((infodisp, 'xmpp.set'), (self, 'out.info.set'), passthrough=2)
        self.link((infodisp, 'xmpp.result'), (self, 'out.info.result'), passthrough=2)
        self.link((infodisp, 'xmpp.error'), (self, 'out.info.error'), passthrough=2)
        self.link((infodisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((infodisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(infodisp)
        infodisp.activate()

        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1
