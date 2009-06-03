# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.protocol.core.message import MessageDispatcher
from headstock.api.jid import JID
from headstock.api import Entity
from headstock.api.im import Message, Body, Event
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS

__all__ = ['make_linkages', 'IMComponent']

class IMComponent(component):
    Inboxes = {"inbox"    : "headstock.api.contact.Message instance received from a peer",
               "outgoing" : "tuple of the form (contact_jid, message)",
               "jid"      : "headstock.api.jid.JID instance received from the server",
               "bound"    : "",
               "control"  : "stops the component"}
    
    Outboxes = {"outbox"  : "headstock.api.im.Message to send to the client",
                "received": "",
                "signal"  : "Shutdown signal"}

    def __init__(self):
        super(IMComponent, self).__init__() 
        self.from_jid = None

    def initComponents(self):
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

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')
            
            if self.dataReady("bound"):
                self.recv('bound')
                self.ready()

            if self.dataReady("outgoing"):
                contact_jid, message = self.recv("outgoing")
                self.send_message(contact_jid, message)

            if self.dataReady("inbox"):
                m = self.recv("inbox")
                self.received_message(m)

            if not self.anyReady():
                self.pause()
  
            yield 1

    def ready(self):
        pass

    def send_message(self, jid, text):
        m = Message(unicode(self.from_jid), unicode(jid), 
                    type=u'chat', stanza_id=generate_unique())
        m.event = Event.composing # note the composing event status
        m.bodies.append(Body(unicode(text)))
        self.send(m, "outbox")
        
        # Right after we sent the first message
        # we send another one reseting the event status
        m = Message(unicode(self.from_jid), unicode(jid), 
                    type=u'chat', stanza_id=generate_unique())
        self.send(m, "outbox")

    def received_message(self, message):
        self.send(message, 'received')

def make_linkages(im_handler_cls=IMComponent):
    linkages = {("xmpp", "%s.message" % XMPP_CLIENT_NS): ("msgdisp", "inbox"),
                ("msgdisp", "log"): ('logger', "inbox"),
                ("msgdisp", "xmpp.normal"): ('msghandler', 'inbox'),
                ("msgdisp", "xmpp.chat"): ('msghandler', 'inbox'),
                ("msghandler", "outbox"): ('msgdisp', 'forward'),
                ('jidsplit', 'chatjid'): ('msghandler', 'jid'),
                ('boundsplit', 'chatbound'): ('msghandler', 'bound'),
                ("msgdisp", "outbox"): ("xmpp", "forward")}
    return dict(msghandler=im_handler_cls(),
                msgdisp=MessageDispatcher()), linkages
