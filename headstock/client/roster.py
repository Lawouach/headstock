# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.protocol.core.roster import RosterDispatcher
from headstock.protocol.core.presence import PresenceDispatcher
from headstock.api.jid import JID
from headstock.api import Entity
from headstock.api.contact import Presence, Roster, Item
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS

__all__ = ['RosterComponent', 'make_linkages']

class RosterComponent(component):    
    Inboxes = {"inbox"        : "headstock.api.contact.Roster instance",
               "control"      : "stops the component",
               "pushed"       : "roster stanzas pushed by the server",
               "remove"       : "",
               "add"          : "",
               "jid"          : "headstock.api.jid.JID instance received from the server",
               "bound"        : "",
               "ask-activity" : "request activity status to the server for each roster contact"}
    
    Outboxes = {"outbox"      : "",
                "signal"      : "Shutdown signal",
                "message"     : "Message to send",
                "roster"      : "",
                "removed"     : "",
                "added"       : "",
                "activity"    : "headstock.api.activity.Activity instance to send to the server"}

    def __init__(self):
        super(RosterComponent, self).__init__() 
        self.from_jid = None

        self.cot = None

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

            if self.dataReady("pushed"):
                roster = self.recv('pushed')
                self.updated_roster(roster)
                    
            if self.dataReady('remove'):
                contact_jid = self.recv('remove')
                self.remove_contact(str(contact_jid))

            if self.dataReady('add'):
                contact_jid, groups = self.recv('add')
                self.add_contact(contact_jid, groups)

            if self.dataReady("inbox"):
                roster = self.recv("inbox")
                self.received_roster(roster)

            if self.dataReady('ask-activity'):
                jid = self.recv('ask-activity')
                self.ask_activity(jid)

            if not self.anyReady():
                self.pause()
  
            yield 1

        self.cleanup()

    def ready(self):
        pass

    def cleanup(self):
        pass

    def updated_roster(self, roster):
        for nodeid in roster.items:
            contact = roster.items[nodeid]
            if contact.subscription in ['remove']:
                self.send(contact, 'removed')
            elif contact.subscription in ['both', 'from', 'none']:
                self.send(contact, 'added')
            self.send(Roster(from_jid=self.from_jid, to_jid=nodeid,
                             type=u'result', stanza_id=generate_unique()),
                      'outbox')

    def remove_contact(self, contact_jid):
        r = Roster(from_jid=self.from_jid, to_jid=contact_jid,
                   type=u'set', stanza_id=generate_unique())
        i = Item(contact_jid)
        i.subscription = u'remove'
        r.items[contact_jid] = i
        self.send(r, 'outbox')

    def add_contact(self, contact_jid, groups=None):
        r = Roster(from_jid=self.from_jid, to_jid=contact_jid,
                   type=u'set', stanza_id=generate_unique())
        i = Item(contact_jid)
        i.subscription = None
        if groups:
            i.groups = groups[:]
        r.items[contact_jid] = i
        self.send(r, 'outbox')

    def received_roster(self, roster):
        self.send(roster, "roster")

    def ask_activity(self, jid):
        a = Activity(unicode(self.from_jid), unicode(jid))
        self.send(a, 'activity')

def make_linkages(roster_handler_cls=RosterComponent):
    linkages = {("xmpp", "%s.query" % XMPP_ROSTER_NS): ("rosterdisp", "inbox"),
                ("rosterdisp", "log"): ('logger', "inbox"),
                ('rosterdisp', 'xmpp.set'): ('rosterhandler', 'pushed'),
                ('rosterdisp', 'xmpp.result'): ('rosterhandler', 'inbox'),
                ('rosterhandler', 'outbox'): ('rosterdisp', 'forward'),
                ('jidsplit', 'contactjid'): ('rosterhandler', 'jid'),
                ('boundsplit', 'contactbound'): ('rosterhandler', 'bound'),
                ("rosterdisp", "outbox"): ("xmpp", "forward")}
    return dict(rosterdisp=RosterDispatcher(), 
                rosterhandler=roster_handler_cls()), linkages
    
