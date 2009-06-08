# -*- coding: utf-8 -*-
import random
import time

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.api.contact import Roster
from headstock.lib.cot import CotManager

from bridge import Element as E
from bridge.common import XMPP_ROSTER_NS

__all__ = ['CotComponent', 'make_linkages']

class CotComponent(component):    
    Inboxes = {"inbox"   : "",
               "control" : "",
               "ping"    : "",
               "jid"     : "",
               "bound"   : ""}
    
    Outboxes = {"outbox" : "",
                "signal" : "",
                "log"    : ""}

    def __init__(self, monitor_freq=3.0):
        super(CotComponent, self).__init__() 
        self.monitor_freq = monitor_freq
        self.from_jid = None
        self.manager = None
        self.roster = None
        self.started = False

    def initComponents(self):
        return 1

    def _send_stanza(self):
        try:
            stanza = self.manager.stanzas.next()
            if stanza:
                stanza = self.fill_stanza(stanza)
                self.send(stanza, 'outbox')
        except StopIteration:
            pass

    def main(self):
        yield self.initComponents()
        
        self.running = True
        while self.running:
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

            if self.dataReady("inbox"):
                e = self.recv('inbox')
                if e.xml_ns == XMPP_ROSTER_NS and \
                       e.xml_parent.get_attribute_value('type') == 'result':
                    roster = Roster.from_element(e)
                    self.roster_updated(roster)
                    if not self.started:
                        self.start_job()
                    
                self.send(('INCOMING', e.xml_parent), 'log')
                self.ack_stanza(e.xml_parent)
                self.send_stanza()

            if self.dataReady("ping"):
                self.recv('ping')
                if self.manager.exhausted:
                    self.completed()
                    
            if self.running and not self.anyReady():
                self.pause()
  
            yield 1

        self.send(producerFinished(), "signal")
        
        yield 1

    def start_job(self):
        self.started = True
        self._send_stanza()

    def roster_updated(self, roster):
        self.roster = roster

    def send_stanza(self):
        self._send_stanza()

    def ack_stanza(self, e):
        self.manager.ack_stanza(self.from_jid, e)

    def fill_stanza(self, stanza):
        from_jid = stanza.get_attribute_value('from')
        if from_jid == '${from-id}':
            stanza.set_attribute_value(u'from', unicode(self.from_jid))

        to_jid = stanza.get_attribute_value('to')
        if to_jid == '${to-id}':
            to_jid = self.pick_contact()
            stanza.set_attribute_value(u'to', unicode(to_jid))
        elif to_jid == '${from-id}':
            stanza.set_attribute_value(u'to', unicode(self.from_jid))

        return stanza

    def pick_contact(self):
        item = random.sample(self.roster.items, 1)
        if item:
            return item[0]

    def completed(self):
        self.running = False

def make_linkages(mapping, manager, cot_handler_cls=CotComponent):
    comp = cot_handler_cls()
    linkages = {("cothandler", "log"): ('logger', "inbox"),
                ("cothandler", "outbox"): ("xmpp", "forward"),
                ("cothandler", "signal"): ("client", "control"),
                ("client", "pong"): ("cothandler", "ping"),
                ('jidsplit', 'cotjid'): ('cothandler', 'jid'),
                ('boundsplit', 'cotbound'): ('cothandler', 'bound')}
    for name, ns in mapping:
        linkages[("xmpp", "%s.%s" % (ns, name))] = ("cothandler", "inbox")
    comp.manager = manager
    return dict(cothandler=comp), linkages
    
