# -*- coding: utf-8 -*-
import random

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.api.contact import Roster
from headstock.lib.cot import CotManager

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS, XMPP_LAST_NS, \
     XMPP_VERSION_NS, XMPP_PUBSUB_NS, XMPP_PUBSUB_OWNER_NS
        
__all__ = ['CotComponent', 'make_linkages']

class CotComponent(component):    
    Inboxes = {"inbox"   : "",
               "control" : "",
               "healthcheck": "",
               "jid"     : "",
               "bound"   : ""}
    
    Outboxes = {"outbox"   : "",
                "signal"   : "",
                "_monitor" : "",
                "log"      : ""}

    def __init__(self, keep_alive=True, timeout=10):
        super(CotComponent, self).__init__()
        self.from_jid = None
        self.manager = None
        self.roster = None
        self.started = False
        self.keep_alive = keep_alive
        self.timeout = timeout

        self.stanza_filler_mapping = {}
        self.stanza_filler_mapping[('iq', XMPP_CLIENT_NS)] = self.fill_iq_expected_stanza
        self.stanza_filler_mapping[('query', XMPP_ROSTER_NS)] = self.fill_roster_expected_stanza
        self.stanza_filler_mapping[('query', XMPP_LAST_NS)] = self.fill_last_expected_stanza
        self.stanza_filler_mapping[('query', XMPP_VERSION_NS)] = self.fill_version_expected_stanza
        self.stanza_filler_mapping[('pubsub', XMPP_PUBSUB_NS)] = self.fill_pubsub_expected_stanza
        self.stanza_filler_mapping[('pubsub', XMPP_PUBSUB_OWNER_NS)] = self.fill_pubsub_expected_stanza

    def initComponents(self):
        if self.timeout > 0:
            from headstock.lib.monitor import ThreadedMonitor
            self.monitor = ThreadedMonitor(self.timeout)
            self.link((self.monitor, 'outbox'), (self, 'healthcheck'))
            self.link((self, '_monitor'), (self.monitor, 'inbox'))
            self.addChildren(self.monitor)
            self.monitor.activate()
        return 1

    def _send_stanza(self):
        try:
            stanza = self.manager.stanzas.next()
            if stanza:
                stanza = self.fill_stanza(stanza)
                self.send(stanza, 'outbox')
        except StopIteration:
            self.manager.exhausted = True
        except Exception, ex:
            self.send(str(ex), 'log')
            raise

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
                iq = e.xml_parent
                
                if e.xml_name == 'iq' and e.xml_ns == XMPP_CLIENT_NS:
                    iq = e
                elif e.xml_ns == XMPP_ROSTER_NS:
                    roster = Roster.from_element(e)
                    self.roster_updated(roster)
                    if not self.started:
                        self.start_job()

                if self.manager.is_expected(iq):
                    self.send(('INCOMING', iq), 'log')
                    self.ack_stanza(iq)
                    self.send_stanza()
                    
                    if not self.keep_alive and self.manager.completed:
                        self.completed()
                    
            if self.dataReady("healthcheck"):
                self.recv("healthcheck")
                if self.manager.completed:
                    self.send(-1, '_monitor')
                    self.removeChild(self.monitor)
                    self.completed()
                else:
                    self.send(self.timeout, '_monitor')
                        
            if self.running and not self.anyReady():
                self.pause()
  
            yield 1

        self.send(producerFinished(), "signal")
        
        yield 1

    def start_job(self):
        self.started = True
        self._send_stanza()

    def pick_contact(self):
        if self.roster.items:
            item = random.sample(self.roster.items, 1)
            if item:
                return item[0]

    def completed(self):
        self.running = False

    def roster_updated(self, roster):
        self.roster = roster

    def send_stanza(self):
        self._send_stanza()

    def ack_stanza(self, e):
        self.manager.ack_stanza(e, self.fill_expected_stanza)

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

        def _traverse(e):
            if (e.xml_name, e.xml_ns) in self.stanza_filler_mapping:
                e = self.stanza_filler_mapping[(e.xml_name, e.xml_ns)](e)
            for child in e.xml_children:
                _traverse(child)

        _traverse(stanza)

        return stanza

    def fill_expected_stanza(self, stanza):
        from_jid = stanza.get_attribute_value('from')
        if from_jid == '${from-id}':
            stanza.set_attribute_value(u'from', unicode(self.from_jid))
            
        to_jid = stanza.get_attribute_value('to')
        if to_jid == '${from-id}':
            stanza.set_attribute_value(u'to', unicode(self.from_jid))

        def _traverse(e):
            if (e.xml_name, e.xml_ns) in self.stanza_filler_mapping:
                e = self.stanza_filler_mapping[(e.xml_name, e.xml_ns)](e)
            for child in e.xml_children:
                _traverse(child)

        _traverse(stanza)

        return stanza

    def fill_iq_expected_stanza(self, stanza):
        return stanza
    
    def fill_roster_expected_stanza(self, stanza):
        return stanza
            
    def fill_version_expected_stanza(self, stanza):
        return stanza
            
    def fill_last_expected_stanza(self, stanza):
        return stanza
            
    def fill_pubsub_expected_stanza(self, stanza):
        def _traverse(e):
            node = e.get_attribute_value('node')
            if node:
                node = unicode(node).replace('${node-id}', self.from_jid.node)
                e.set_attribute_value(u'node', node)

            for child in e.xml_children:
                _traverse(child)
                
        _traverse(stanza)
        return stanza
            
def make_linkages(manager, cot_handler_cls=CotComponent):
    comp = cot_handler_cls()
    linkages = {("cothandler", "log"): ('logger', "inbox"),
                ("cothandler", "outbox"): ("xmpp", "forward"),
                ("cothandler", "signal"): ("client", "control"),
                ('jidsplit', 'cotjid'): ('cothandler', 'jid'),
                ('boundsplit', 'cotbound'): ('cothandler', 'bound')}
    mapping = []
    mapping.append(('iq', XMPP_CLIENT_NS))
    mapping.append(('query', XMPP_ROSTER_NS))

    for name, ns in mapping:
        linkages[("xmpp", "%s.%s" % (ns, name))] = ("cothandler", "inbox")
        
    comp.manager = manager
    return dict(cothandler=comp), linkages
    
