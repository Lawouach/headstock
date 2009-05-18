# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.lib.cot import CotManager

from bridge import Element as E

__all__ = ['CotComponent', 'make_linkages']

def make_linkages(cots):
    comp = CotComponent()
    linkages = {("cothandler", "log"): ('logger', "inbox"),
                ("cothandler", "outbox"): ("xmpp", "forward"),
                ("cothandler", "signal"): ("client", "control"),
                ('jidsplit', 'cotjid'): ('cothandler', 'jid'),
                ('boundsplit', 'cotbound'): ('cothandler', 'bound')}
    for name, ns, cot in cots:
        linkages[("xmpp", "%s.%s" % (ns, name))] = ("cothandler", "inbox")
        comp.cots.add(cot)
    return dict(cothandler=comp), linkages
    
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

        self.stanzas = self.cots.run()

    def initComponents(self):
        return 1

    def send_stanza(self):
        try:
            stanza = self.stanzas.next()
            self.send(stanza, 'outbox')
        except StopIteration:
            pass

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
                self.send_stanza()
                
            if self.dataReady("inbox"):
                e = self.recv('inbox')
                self.send(('INCOMING', e.xml_parent), 'log')
                self.cots.ack_stanza(e.xml_parent)
                self.send_stanza()

            if self.cots.completed:
                self.send(producerFinished(), "signal")
                break
                
            if not self.anyReady():
                self.pause()
  
            yield 1

        self.cots.report()
