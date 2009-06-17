# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.protocol.core.presence import PresenceDispatcher
from headstock.api.jid import JID
from headstock.api import Entity
from headstock.api.contact import Presence
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS

__all__ = ['PresenceComponent', 'make_linkages']

class PresenceComponent(component):
    Inboxes = {"inbox"       : "headstock.api.contact.Presence instance",
               "control"     : "Shutdown the client stream",
               "jid"          : "headstock.api.jid.JID instance received from the server",
               "available"   : "",
               "unavailable" : "",
               "requestedsub"   : "Received subscription from a peer",
               "requestedunsub" : "Received unsubscription from a peer",
               "acceptsub"   : "Accepted subscription",
               "rejectsub"   : "Rejected subscription",
               "requestsub"  : "Request subscription to a peer",
               "requestunsub"  : "Request unsubscription to a peer"}
    
    Outboxes = {"outbox" : "headstock.api.contact.Presence instance to return to the server",
                "signal" : "Shutdown signal",
                "contactavailable": "",
                "contactunavailable": "",
                "subrequested": "",
                "unsubrequested": "",
                "log"    : "log",}
    
    def __init__(self):
        super(PresenceComponent, self).__init__()

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
            
            if self.dataReady("available"):
                p = self.recv("available")
                self.contact_available(p)

            if self.dataReady("unavailable"):
                p = self.recv("unavailable")
                self.contact_unavailable(p)

            if self.dataReady("requestedsub"):
                p = self.recv("requestedsub")
                self.subscription_requested(p)

            if self.dataReady("requestedunsub"):
                p = self.recv("requestedunsub")
                self.unsubscription_requested(p)

            if self.dataReady("acceptsub"):
                to_jid = self.recv("acceptsub")
                self.accept_subscription(to_jid)

            if self.dataReady("rejectsub"):
                to_jid = self.recv("rejectsub")
                self.reject_subscription(to_jid)

            if self.dataReady("requestsub"):
                to_jid = self.recv("requestsub")
                self.request_subscription(to_jid)

            if self.dataReady("requestunsub"):
                to_jid = self.recv("requestunsub")
                self.request_unsubscription(to_jid)

            if not self.anyReady():
                self.pause()
  
            yield 1

    def contact_available(self, p):
        self.send(p, 'contactavailable')

    def contact_unavailable(self, p):
        self.send(p, 'contactunavailable')

    def subscription_requested(self, p):
        p.swap_jids()
        self.send(p, "subrequested")

    def unsubscription_requested(self, p):
        p.swap_jids()
        self.send(p, "unsubrequested")

    def accept_subscription(self, jid):
        p = Presence(from_jid=self.from_jid, to_jid=unicode(jid),
                     type=u'subscribed')
        self.send(p, "outbox")

    def reject_subscription(self, jid):
        p = Presence(from_jid=self.from_jid, to_jid=unicode(jid),
                     type=u'unsubscribed')
        self.send(p, "outbox")

    def request_subscription(self, jid):
        p = Presence(from_jid=self.from_jid, to_jid=unicode(jid),
                     type=u'subscribe')
        self.send(p, "outbox")
        
    def request_subscription(self, jid):
        p = Presence(from_jid=self.from_jid, to_jid=unicode(jid),
                     type=u'unsubscribe')
        self.send(p, "outbox")
        

def make_linkages(presence_handler_cls=PresenceComponent):
    linkages = {("xmpp", "%s.presence" % XMPP_CLIENT_NS): ("presencedisp", "inbox"),
                ("presencedisp", "log"): ('logger', "inbox"),
                ("presencedisp", "xmpp.available"): ("presencehandler", "available"),
                ("presencedisp", "xmpp.unavailable"): ("presencehandler", "unavailable"),
                ("presencedisp", "xmpp.subscribe"): ("presencehandler", "requestedsub"),
                ("presencedisp", "xmpp.unsubscribe"): ("presencehandler", "requestedunsub"),
                ("presencehandler", "outbox"): ("presencedisp", "forward"),
                ('jidsplit', 'presencejid'): ('presencehandler', 'jid'),
                ("presencedisp", "outbox"): ("xmpp", "forward")}
    return dict(presencedisp=PresenceDispatcher(),
                presencehandler=presence_handler_cls()), linkages
