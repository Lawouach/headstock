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

def make_linkages():
    linkages = {("xmpp", "%s.query" % XMPP_ROSTER_NS): ("rosterdisp", "inbox"),
                ("rosterdisp", "log"): ('logger', "inbox"),
                ('rosterdisp', 'xmpp.set'): ('rosterhandler', 'pushed'),
                ('rosterdisp', 'xmpp.result'): ('rosterhandler', 'inbox'),
                ('rosterhandler', 'outbox'): ('rosterdisp', 'forward'),
                ('jidsplit', 'contactjid'): ('rosterhandler', 'jid'),
                ('boundsplit', 'contactbound'): ('rosterhandler', 'bound'),
                ("rosterdisp", "outbox"): ("xmpp", "forward")}
    return dict(rosterdisp=RosterDispatcher(),
                rosterhandler=RosterComponent()), linkages
    
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
                "added"     : "",
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

            if self.dataReady("pushed"):
                roster = self.recv('pushed')
                for nodeid in roster.items:
                    contact = roster.items[nodeid]
                    if contact.subscription in ['remove']:
                        self.send(contact, 'removed')
                    elif contact.subscription in ['both', 'from', 'none']:
                        self.send(contact, 'added')
                    self.send(Roster(from_jid=self.from_jid, to_jid=nodeid,
                                     type=u'result', stanza_id=generate_unique()),
                              'outbox')
                    
            if self.dataReady('remove'):
                contact_jid = self.recv('remove')
                contact_jid = str(contact_jid)
                r = Roster(from_jid=self.from_jid, to_jid=contact_jid,
                           type=u'set', stanza_id=generate_unique())
                i = Item(contact_jid)
                i.subscription = u'remove'
                r.items[contact_jid] = i
                self.send(r, 'outbox')

            if self.dataReady('add'):
                contact_jid, groups = self.recv('add')
                r = Roster(from_jid=self.from_jid, to_jid=contact_jid,
                           type=u'set', stanza_id=generate_unique())
                i = Item(contact_jid)
                i.subscription = None
                i.groups = groups[:]
                r.items[contact_jid] = i
                self.send(r, 'outbox')

            if self.dataReady("inbox"):
                roster = self.recv("inbox")
                self.send(roster, "roster")

            if self.dataReady('ask-activity'):
                jid = self.recv('ask-activity')
                if not jid and self.roster:
                    for nodeid in self.roster.items:
                        contact = roster.items[nodeid]
                        a = Activity(unicode(self.from_jid), unicode(contact.jid))
                        self.send(a, 'activity')
                elif jid:
                    a = Activity(unicode(self.from_jid), unicode(jid))
                    self.send(a, 'activity')

            if not self.anyReady():
                self.pause()
  
            yield 1
