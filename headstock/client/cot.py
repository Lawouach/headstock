# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.lib.cot import CotManager

from bridge import Element as E

__all__ = ['CotComponent', 'make_linkages']

class CotComponent(component):    
    Inboxes = {"inbox"   : "",
               "control" : "",
               "jid"     : "",
               "bound"   : ""}
    
    Outboxes = {"outbox" : "",
                "signal" : "",
                "log"    : ""}

    def __init__(self):
        super(CotComponent, self).__init__() 
        self.from_jid = None
        self.cots = CotManager()

    def initComponents(self):
        return 1

    def _send_stanza(self):
        try:
            stanza = self.cots.stanzas.next()
            print "OUT:", stanza.xml()
            if stanza:
                self.send(stanza, 'outbox')
        except StopIteration:
            self.cots.exhausted = True
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
                self.send_stanza()
                
            if self.dataReady("inbox"):
                e = self.recv('inbox')
                self.send(('INCOMING', e.xml_parent), 'log')
                self.send_stanza()
                self.ack_stanza(e.xml_parent)

            if self.cots.completed:
                self.completed()

            if not self.anyReady() and self.running:
                self.pause()
  
            yield 1

    def start_job(self):
        self._send_stanza()

    def send_stanza(self):
        self._send_stanza()

    def ack_stanza(self, e):
        self.cots.ack_stanza(e)

    def completed(self):
        self.send(producerFinished(), "signal")
        self.running = False

def make_linkages(cots, cot_handler_cls=CotComponent):
    comp = cot_handler_cls()
    linkages = {("cothandler", "log"): ('logger', "inbox"),
                ("cothandler", "outbox"): ("xmpp", "forward"),
                ("cothandler", "signal"): ("client", "control"),
                ('jidsplit', 'cotjid'): ('cothandler', 'jid'),
                ('boundsplit', 'cotbound'): ('cothandler', 'bound')}
    for name, ns, manager in cots:
        linkages[("xmpp", "%s.%s" % (ns, name))] = ("cothandler", "inbox")
        comp.cots = manager
    return dict(cothandler=comp), linkages
    
