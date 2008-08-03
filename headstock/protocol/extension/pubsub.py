# -*- coding: utf-8 -*-

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished
from Kamaelia.Chassis.Graphline import Graphline

from bridge.common import XMPP_PUBSUB_NS, XMPP_DISCO_INFO_NS, \
     XMPP_DISCO_ITEMS_NS, XMPP_PUBSUB_OWNER_NS, XMPP_PUBSUB_EVENT_NS
from headstock.api.pubsub import Node, Message

__all__ = ['SubscriptionDispatcher', 'NodeCreationDispatcher',
           'NodeDeletionDispatcher', 'UnsubscriptionDispatcher', 
           'ItemPublicationDispatcher', 'ItemDeletionDispatcher',
           'MessageEventDispatcher', 'NodePurgeDispatcher',
           'PubSubDispatcher', 'ItemRetrievalDispatcher']

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

class NodePurgeDispatcher(component):
    
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
       super(NodePurgeDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                s = self.recv("forward")
                self.send(Node.to_purge_element(s), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")

                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Node.from_purge_element(e), key)
                    handled = True

                if not handled:
                    self.send(e, "unknown")
                    
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1

class ItemRetrievalDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.get"     : "Activity requests",
                "xmpp.set"     : "Activity responses",
                "xmpp.result"  : "Activity responses",
                "xmpp.error"   : "Activity response error",
                "xmpp.all.get"     : "Activity requests",
                "xmpp.all.set"     : "Activity responses",
                "xmpp.all.result"  : "Activity responses",
                "xmpp.all.error"   : "Activity response error",
                }
    
    def __init__(self):
       super(ItemRetrievalDispatcher, self).__init__() 

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
                self.send(Node.to_request_item(s), "outbox")

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent.xml_parent
                self.send(('INCOMING', e), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'get'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Node.from_request_item(e), key)
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

class MessageEventDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "",}
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.message" : "Activity requests",
                "xmpp.message.purge" : "Activity requests",
                }
    
    def __init__(self):
       super(MessageEventDispatcher, self).__init__() 

    def main(self):
        yield 1

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                handled = False
                a = self.recv("inbox")
                e = a.xml_parent
                self.send(('INCOMING', e), "log")

                m = Message.from_element(e)

                if m.event == 'items':
                    self.send(m, "xmpp.message")
                elif m.event == 'purge':
                    self.send(m, "xmpp.message.purge")
                else:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1

class PubSubDispatcher(component):
    Inboxes = {"inbox"               : "bridge.Element instance",
               "control"             : "Shutdown the client stream",
               "retrieve.inbox"        : "",
               "retrieve.forward"      : "",
               "retrieve.all.inbox"      : "",
               "retrieve.all.forward"      : "",
               "create.inbox"        : "",
               "create.forward"      : "",
               "purge.inbox"        : "",
               "purge.forward"      : "",
               "delete.inbox"        : "",
               "delete.forward"      : "",
               "subscribe.inbox"     : "",
               "subscribe.forward"   : "",
               "unsubscribe.inbox"   : "",
               "unsubscribe.forward"  : "",
               "publish.inbox"       : "",
               "publish.forward"     : "",
               "retract.inbox"       : "",
               "retract.forward"     : "",
               "message.inbox"       : "",
               "in.retrieve.error"        : "Retrieve items response error",
               "in.retrieve.get"          : "Retrieve items requests",
               "in.retrieve.set"          : "Retrieve items responses",
               "in.retrieve.result"       : "Retrieve items responses",
               "in.retrieve.all.error"        : "Retrieve items response error",
               "in.retrieve.all.get"          : "Retrieve items requests",
               "in.retrieve.all.set"          : "Retrieve items responses",
               "in.retrieve.all.result"       : "Retrieve items responses",
               "in.create.error"        : "Publish items response error",
               "in.create.get"          : "Publish items requests",
               "in.create.set"          : "Publish items responses",
               "in.create.result"       : "Publish items responses",
               "in.purge.error"        : "Publish items response error",
               "in.purge.get"          : "Publish items requests",
               "in.purge.set"          : "Publish items responses",
               "in.purge.result"       : "Publish items responses",
               "in.delete.error"        : "Publish items response error",
               "in.delete.get"          : "Publish items requests",
               "in.delete.set"          : "Publish items responses",
               "in.delete.result"       : "Publish items responses",
               "in.subscribe.get"       : "Publish items requests",
               "in.subscribe.set"       : "Publish items responses",
               "in.subscribe.result"    : "Publish items responses",
               "in.subscribe.error"     : "Publish items response error",
               "in.unsubscribe.get"     : "Publish items requests",
               "in.unsubscribe.set"     : "Publish items responses",
               "in.unsubscribe.result"  : "Publish items responses",
               "in.unsubscribe.error"   : "Publish items response error",
               "in.publish.get"         : "Publish items requests",
               "in.publish.set"         : "Publish items responses",
               "in.publish.result"      : "Publish items responses",
               "in.publish.error"       : "Publish items response error",
               "in.retract.get"         : "Retract item requests",
               "in.retract.set"         : "Retract item responses",
               "in.retract.result"      : "Retract item responses",
               "in.retract.error"       : "Retract item response error"}
    
    Outboxes = {"outbox"                  : "bridge.Element instance",
                "signal"                  : "Shutdown signal",
                "unknown"                 : "Unknown element that could not be dispatched properly",
                "log"                     : "log",
                "retrieve.outbox"           : "",
                "retrieve.all.outbox"           : "",
                "create.outbox"           : "",
                "purge.outbox"            : "",
                "delete.outbox"           : "",
                "subscribe.outbox"        : "",
                "unsubscribe.outbox"      : "",
                "publish.outbox"          : "",
                "retract.outbox"          : "",
                "message.outbox"          : "",
                "out.retrieve.error"       : "Retrieve items responses",
                "out.retrieve.get"          : "Retrieve items requests",
                "out.retrieve.set"          : "Retrieve items responses",
                "out.retrieve.result"       : "Retrieve items responses",
                "out.retrieve.all.error"       : "Retrieve items responses",
                "out.retrieve.all.get"          : "Retrieve items requests",
                "out.retrieve.all.set"          : "Retrieve items responses",
                "out.retrieve.all.result"       : "Retrieve items responses",
                "out.create.get"          : "Publish items requests",
                "out.create.set"          : "Publish items responses",
                "out.create.result"       : "Publish items responses",
                "out.purge.error"        : "Publish items response error",
                "out.purge.get"          : "Publish items requests",
                "out.purge.set"          : "Publish items responses",
                "out.purge.result"       : "Publish items responses",
                "out.delete.error"        : "Publish items response error",
                "out.delete.get"          : "Publish items requests",
                "out.delete.set"          : "Publish items responses",
                "out.delete.result"       : "Publish items responses",
                "out.create.error"        : "Publish items response error",
                "out.subscribe.get"       : "Publish items requests",
                "out.subscribe.set"       : "Publish items responses",
                "out.subscribe.result"    : "Publish items responses",
                "out.subscribe.error"     : "Publish items response error",
                "out.unsubscribe.get"     : "Publish items requests",
                "out.unsubscribe.set"     : "Publish items responses",
                "out.unsubscribe.result"  : "Publish items responses",
                "out.unsubscribe.error"   : "Publish items response error",
                "out.publish.get"         : "Publish items requests",
                "out.publish.set"         : "Publish items responses",
                "out.publish.result"      : "Publish items responses",
                "out.publish.error"       : "Publish items response error",
                "out.retract.get"         : "Retract item requests",
                "out.retract.set"         : "Retract item responses",
                "out.retract.result"      : "Retract item responses",
                "out.retract.error"       : "Retract item response error",
                "out.message"             : "Retract item requests",
                "out.message.purge"       : "Retract item requests",}
    
    def __init__(self):
       super(PubSubDispatcher, self).__init__() 

    def initComponents(self):
        subdisp = SubscriptionDispatcher()
        self.link((self, 'subscribe.inbox'), (subdisp, 'inbox'), passthrough=1)
        self.link((self, 'subscribe.forward'), (subdisp, 'forward'), passthrough=1)
        self.link((self, 'in.subscribe.get'), (subdisp, 'forward'), passthrough=1)
        self.link((self, 'in.subscribe.set'), (subdisp, 'forward'), passthrough=1)
        self.link((self, 'in.subscribe.result'), (subdisp, 'forward'), passthrough=1)
        self.link((self, 'in.subscribe.error'), (subdisp, 'forward'), passthrough=1)
        self.link((subdisp, 'outbox'), (self, 'subscribe.outbox'), passthrough=2)
        self.link((subdisp, 'xmpp.get'), (self, 'out.subscribe.get'), passthrough=2)
        self.link((subdisp, 'xmpp.set'), (self, 'out.subscribe.set'), passthrough=2)
        self.link((subdisp, 'xmpp.result'), (self, 'out.subscribe.result'), passthrough=2)
        self.link((subdisp, 'xmpp.error'), (self, 'out.subscribe.error'), passthrough=2)
        self.link((subdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((subdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(subdisp)
        subdisp.activate()

        unsubdisp = UnsubscriptionDispatcher()
        self.link((self, 'unsubscribe.inbox'), (unsubdisp, 'inbox'), passthrough=1)
        self.link((self, 'unsubscribe.forward'), (unsubdisp, 'forward'), passthrough=1)
        self.link((self, 'in.unsubscribe.get'), (unsubdisp, 'forward'), passthrough=1)
        self.link((self, 'in.unsubscribe.set'), (unsubdisp, 'forward'), passthrough=1)
        self.link((self, 'in.unsubscribe.result'), (unsubdisp, 'forward'), passthrough=1)
        self.link((self, 'in.unsubscribe.error'), (unsubdisp, 'forward'), passthrough=1)
        self.link((unsubdisp, 'outbox'), (self, 'unsubscribe.outbox'), passthrough=2)
        self.link((unsubdisp, 'xmpp.get'), (self, 'out.unsubscribe.get'), passthrough=2)
        self.link((unsubdisp, 'xmpp.set'), (self, 'out.unsubscribe.set'), passthrough=2)
        self.link((unsubdisp, 'xmpp.result'), (self, 'out.unsubscribe.result'), passthrough=2)
        self.link((unsubdisp, 'xmpp.error'), (self, 'out.unsubscribe.error'), passthrough=2)
        self.link((unsubdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((unsubdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(unsubdisp)
        unsubdisp.activate()

        nodecreatedisp = NodeCreationDispatcher()
        self.link((self, 'create.inbox'), (nodecreatedisp, 'inbox'), passthrough=1)
        self.link((self, 'create.forward'), (nodecreatedisp, 'forward'), passthrough=1)
        self.link((self, 'in.create.get'), (nodecreatedisp, 'forward'), passthrough=1)
        self.link((self, 'in.create.set'), (nodecreatedisp, 'forward'), passthrough=1)
        self.link((self, 'in.create.result'), (nodecreatedisp, 'forward'), passthrough=1)
        self.link((self, 'in.create.error'), (nodecreatedisp, 'forward'), passthrough=1)
        self.link((nodecreatedisp, 'outbox'), (self, 'create.outbox'), passthrough=2)
        self.link((nodecreatedisp, 'xmpp.get'), (self, 'out.create.get'), passthrough=2)
        self.link((nodecreatedisp, 'xmpp.set'), (self, 'out.create.set'), passthrough=2)
        self.link((nodecreatedisp, 'xmpp.result'), (self, 'out.create.result'), passthrough=2)
        self.link((nodecreatedisp, 'xmpp.error'), (self, 'out.create.error'), passthrough=2)
        self.link((nodecreatedisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((nodecreatedisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(nodecreatedisp)
        nodecreatedisp.activate()

        nodepurgedisp = NodePurgeDispatcher()
        self.link((self, 'purge.inbox'), (nodepurgedisp, 'inbox'), passthrough=1)
        self.link((self, 'purge.forward'), (nodepurgedisp, 'forward'), passthrough=1)
        self.link((self, 'in.purge.get'), (nodepurgedisp, 'forward'), passthrough=1)
        self.link((self, 'in.purge.set'), (nodepurgedisp, 'forward'), passthrough=1)
        self.link((self, 'in.purge.result'), (nodepurgedisp, 'forward'), passthrough=1)
        self.link((self, 'in.purge.error'), (nodepurgedisp, 'forward'), passthrough=1)
        self.link((nodepurgedisp, 'outbox'), (self, 'purge.outbox'), passthrough=2)
        self.link((nodepurgedisp, 'xmpp.get'), (self, 'out.purge.get'), passthrough=2)
        self.link((nodepurgedisp, 'xmpp.set'), (self, 'out.purge.set'), passthrough=2)
        self.link((nodepurgedisp, 'xmpp.result'), (self, 'out.purge.result'), passthrough=2)
        self.link((nodepurgedisp, 'xmpp.error'), (self, 'out.purge.error'), passthrough=2)
        self.link((nodepurgedisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((nodepurgedisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(nodepurgedisp)
        nodepurgedisp.activate()

        nodedeletedisp = NodeDeletionDispatcher()
        self.link((self, 'delete.inbox'), (nodedeletedisp, 'inbox'), passthrough=1)
        self.link((self, 'delete.forward'), (nodedeletedisp, 'forward'), passthrough=1)
        self.link((self, 'in.delete.get'), (nodedeletedisp, 'forward'), passthrough=1)
        self.link((self, 'in.delete.set'), (nodedeletedisp, 'forward'), passthrough=1)
        self.link((self, 'in.delete.result'), (nodedeletedisp, 'forward'), passthrough=1)
        self.link((self, 'in.delete.error'), (nodedeletedisp, 'forward'), passthrough=1)
        self.link((nodedeletedisp, 'outbox'), (self, 'delete.outbox'), passthrough=2)
        self.link((nodedeletedisp, 'xmpp.get'), (self, 'out.delete.get'), passthrough=2)
        self.link((nodedeletedisp, 'xmpp.set'), (self, 'out.delete.set'), passthrough=2)
        self.link((nodedeletedisp, 'xmpp.result'), (self, 'out.delete.result'), passthrough=2)
        self.link((nodedeletedisp, 'xmpp.error'), (self, 'out.delete.error'), passthrough=2)
        self.link((nodedeletedisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((nodedeletedisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(nodedeletedisp)
        nodedeletedisp.activate()

        itemretrievedisp = ItemRetrievalDispatcher()
        self.link((self, 'retrieve.inbox'), (itemretrievedisp, 'inbox'), passthrough=1)
        self.link((self, 'retrieve.forward'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'in.retrieve.get'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'in.retrieve.set'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'in.retrieve.result'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'in.retrieve.error'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'retrieve.all.inbox'), (itemretrievedisp, 'inbox'), passthrough=1)
        self.link((self, 'retrieve.all.forward'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'in.retrieve.all.get'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'in.retrieve.all.set'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'in.retrieve.all.result'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((self, 'in.retrieve.all.error'), (itemretrievedisp, 'forward'), passthrough=1)
        self.link((itemretrievedisp, 'outbox'), (self, 'retrieve.outbox'), passthrough=2)
        self.link((itemretrievedisp, 'xmpp.get'), (self, 'out.retrieve.get'), passthrough=2)
        self.link((itemretrievedisp, 'xmpp.set'), (self, 'out.retrieve.set'), passthrough=2)
        self.link((itemretrievedisp, 'xmpp.result'), (self, 'out.retrieve.result'), passthrough=2)
        self.link((itemretrievedisp, 'xmpp.error'), (self, 'out.retrieve.error'), passthrough=2)
        self.link((itemretrievedisp, 'xmpp.all.get'), (self, 'out.retrieve.all.get'), passthrough=2)
        self.link((itemretrievedisp, 'xmpp.all.set'), (self, 'out.retrieve.all.set'), passthrough=2)
        self.link((itemretrievedisp, 'xmpp.all.result'), (self, 'out.retrieve.all.result'), passthrough=2)
        self.link((itemretrievedisp, 'xmpp.all.error'), (self, 'out.retrieve.all.error'), passthrough=2)
        self.link((itemretrievedisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((itemretrievedisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(itemretrievedisp)
        itemretrievedisp.activate()

        itempublishdisp = ItemPublicationDispatcher()
        self.link((self, 'publish.inbox'), (itempublishdisp, 'inbox'), passthrough=1)
        self.link((self, 'publish.forward'), (itempublishdisp, 'forward'), passthrough=1)
        self.link((self, 'in.publish.get'), (itempublishdisp, 'forward'), passthrough=1)
        self.link((self, 'in.publish.set'), (itempublishdisp, 'forward'), passthrough=1)
        self.link((self, 'in.publish.result'), (itempublishdisp, 'forward'), passthrough=1)
        self.link((self, 'in.publish.error'), (itempublishdisp, 'forward'), passthrough=1)
        self.link((itempublishdisp, 'outbox'), (self, 'publish.outbox'), passthrough=2)
        self.link((itempublishdisp, 'xmpp.get'), (self, 'out.publish.get'), passthrough=2)
        self.link((itempublishdisp, 'xmpp.set'), (self, 'out.publish.set'), passthrough=2)
        self.link((itempublishdisp, 'xmpp.result'), (self, 'out.publish.result'), passthrough=2)
        self.link((itempublishdisp, 'xmpp.error'), (self, 'out.publish.error'), passthrough=2)
        self.link((itempublishdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((itempublishdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(itempublishdisp)
        itempublishdisp.activate()

        itemretractdisp = ItemDeletionDispatcher()
        self.link((self, 'retract.inbox'), (itemretractdisp, 'inbox'), passthrough=1)
        self.link((self, 'retract.forward'), (itemretractdisp, 'forward'), passthrough=1)
        self.link((self, 'in.retract.get'), (itemretractdisp, 'forward'), passthrough=1)
        self.link((self, 'in.retract.set'), (itemretractdisp, 'forward'), passthrough=1)
        self.link((self, 'in.retract.result'), (itemretractdisp, 'forward'), passthrough=1)
        self.link((self, 'in.retract.error'), (itemretractdisp, 'forward'), passthrough=1)
        self.link((itemretractdisp, 'outbox'), (self, 'retract.outbox'), passthrough=2)
        self.link((itemretractdisp, 'xmpp.get'), (self, 'out.retract.get'), passthrough=2)
        self.link((itemretractdisp, 'xmpp.set'), (self, 'out.retract.set'), passthrough=2)
        self.link((itemretractdisp, 'xmpp.result'), (self, 'out.retract.result'), passthrough=2)
        self.link((itemretractdisp, 'xmpp.error'), (self, 'out.retract.error'), passthrough=2)
        self.link((itemretractdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((itemretractdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(itemretractdisp)
        itemretractdisp.activate()

        msgdisp = MessageEventDispatcher()
        self.link((self, 'message.inbox'), (msgdisp, 'inbox'), passthrough=1)
        self.link((msgdisp, 'xmpp.message'), (self, 'out.message'), passthrough=2)
        self.link((msgdisp, 'xmpp.message.purge'), (self, 'out.message.purge'), passthrough=2)
        self.link((msgdisp, 'unknown'), (self, 'unknown'), passthrough=2)
        self.link((msgdisp, 'log'), (self, 'log'), passthrough=2)
        self.addChildren(msgdisp)
        msgdisp.activate()

        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1
