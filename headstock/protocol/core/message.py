#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.api.im import Message

__all__ = ['MessageDispatcher', 'MessageEchoer']

class MessageDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Message instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance",
                "signal"       : "Shutdown signal",
                "log"          : "log",
                "unknown"      : "Unknown element that could not be dispatched properly",
                "xmpp.normal"  : "Normal message received form client",
                "xmpp.chat"    : "Chat message received from client",
                }
    
    def __init__(self):
       super(MessageDispatcher, self).__init__()

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                m = self.recv("forward")
                self.send(Message.to_element(m), "outbox")

            if self.dataReady("inbox"):
                handled = False
                e = self.recv("inbox")
                self.send(('INCOMING', e.xml(indent=False, omit_declaration=True)), "log")
                
                msg_type = e.get_attribute_value(u'type') or 'normal'
                key = 'xmpp.%s' % unicode(msg_type)

                if key in self.outboxes:
                    self.send(Message.from_element(e), key)
                    e.forget()
                    handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1


class MessageEchoer(component):    
    Inboxes = {"inbox"              : "headstock.api.contact.Message instance to be echoed back",
               "control"            : "Shutdown the client stream",
               }
    
    Outboxes = {"outbox"       : "bridge.Element instance generated from the Message instance",
                "signal"       : "Shutdown signal",
                }

    def __init__(self):
        """Dummy message echoer only when the message has a subject and/or a body"""
        super(MessageEchoer, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                m = self.recv("inbox")
                if m.bodies or m.subjects:
                    m.swap_jids()
                    self.send(Message.to_element(m), "outbox")

            if not self.anyReady():
                self.pause()
  
            yield 1
