#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.protocol.core.stanza import Stanza
from headstock.api.contact import Presence

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS

__all__ = ['PresenceDispatcher', 'PresenceSubscriber']

# Helper function
def create_presence(from_jid=None, to_jid=None, presence_type=None, status=None, show=None):
    stanza = Stanza(u'presence', from_jid, to_jid, presence_type)
    if status:
        E(u'status', content=status, namespace=stanza.xml_ns, parent=stanza)
    if show:
        E(u'show', content=show, namespace=stanza.xml_ns, parent=stanza)
        
    return stanza.to_element()
    
class PresenceDispatcher(component):
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Presence instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"            : "bridge.Element instance to sent back to the client",
                "signal"            : "Shutdown signal",
                "log"               : "log",
                "unknown"           : "Unknown element that could not be dispatched properly",
                "xmpp.error"        : "An error has occurred regarding processing or delivery of a presence stanza",
                "xmpp.probe"        : "Server to server message to check the presence of an entity",
                "xmpp.subscribe"    : "Sender wishes to subscribe to the recipient's presence",
                "xmpp.subscribed"   : "Sender has allowed the recipient to receive their presence",
                "xmpp.unsubscribe"  : "Sender is unsubscribing from another entity's presence",
                "xmpp.unsubscribed" : "Subscription request has been denied or a previously-granted subscription has been cancelled"
                }
    
    def __init__(self):
        super(PresenceDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                p = self.recv("forward")
                self.send(Presence.to_element(p), "outbox")

            if self.dataReady("inbox"):
                e = self.recv("inbox")
                self.send(('INCOMING', e), "log")
                presence_type = e.get_attribute(u'type')
                handled = False
                if presence_type:
                    key = 'xmpp.%s' % presence_type
                    if key in self.outboxes:
                        self.send(Presence.from_element(e), key)
                        handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1

class PresenceSubscriber(component):
    Inboxes = {"inbox"              : "headstock.api.contact.Presence instance",
               "control"            : "Shutdown the client stream",
               }
    
    Outboxes = {"outbox"            : "bridge.Element instance to sent back to the client",
                "signal"            : "Shutdown signal",
                }
    
    def __init__(self, subscribe_cb):
        """
        Component that handles passing the message to the server that a subscribtion
        was either allowed or refused.

        The ``subscribe_cb`` must be a callable that takes a headstock.api.contact.Presence instance
        and returns either that instance to allow the subscription or None to reject it.
        """
        super(PresenceSubscriber, self).__init__()
        self.subscribe_cb = subscribe_cb

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                p = self.recv("inbox")

                action = self.subscribe_cb(p)
                if action == None:
                    e = create_presence(to_jid=unicode(p.to_jid),
                                        presence_type=u'unsubscribed')
                else:
                    # action is now the new instance of 'p' and may have been
                    # modified by the callback function
                    e = create_presence(to_jid=unicode(action.to_jid),
                                        presence_type=u'subscribed')

                self.send(e, "outbox")
                
            if not self.anyReady():
                self.pause()
  
            yield 1
    

class PresenceUnsubscriber(component):
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               }
    
    Outboxes = {"outbox"            : "bridge.Element instance to sent back to the client",
                "signal"            : "Shutdown signal",
                "log"               : "log",
                }
    
    def __init__(self):
       super(PresenceUnsubscriber, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                e = self.recv("inbox")
                
            if not self.anyReady():
                self.pause()
  
            yield 1
    
