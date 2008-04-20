# -*- coding: utf-8 -*-

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from bridge.common import XMPP_PUBSUB_NS, XMPP_DISCO_INFO_NS, \
     XMPP_DISCO_ITEMS_NS, XMPP_PUBSUB_OWNER_NS, XMPP_PUBSUB_EVENT_NS
from headstock.api.pubsub import Node

__all__ = ['SubscriptionDispatcher', 'NodeCreationDispatcher',
           'NodeDeletionDispatcher', 'UnsubscriptionDispatcher', 
           'ItemPublicationDispatcher', 'ItemDeletionDispatcher']

class SubscriptionDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity responses",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(SubscriptionDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                s = self.recv("forward")
                self.send(Node.to_subscription_element(s), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Node.from_subscription_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")
                    
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1

class UnsubscriptionDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity responses",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(UnsubscriptionDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                s = self.recv("forward")
                self.send(Node.to_unsubscription_element(s), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Node.from_unsubscription_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")
                    
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1

class NodeCreationDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity responses",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(NodeCreationDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                s = self.recv("forward")
                self.send(Node.to_creation_element(s), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Node.from_creation_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")
                    
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1

class NodeDeletionDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity responses",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(NodeDeletionDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                s = self.recv("forward")
                self.send(Node.to_deletion_element(s), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Node.from_deletion_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")
                    
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1

class ItemPublicationDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity responses",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(ItemPublicationDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                s = self.recv("forward")
                self.send(Node.to_publication_element(s), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Node.from_publication_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")
                    
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1

class ItemDeletionDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity responses",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(ItemDeletionDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                s = self.recv("forward")
                self.send(Node.to_retract_element(s), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Node.from_retract_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")
                    
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1
