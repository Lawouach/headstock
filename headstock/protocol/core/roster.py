#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.protocol.core.stanza import Stanza
from headstock.protocol.core.iq import Iq
from headstock.lib.utils import generate_unique
from headstock.api.contact import Roster

#####################################################################################
# From RFC 3921
# In XMPP, one's contact list is called a roster, which consists of any number of
# specific roster items, each roster item being identified by a unique JID.
# A user's roster is stored by the user's server on the user's behalf so that
# the user may access roster information from any resource.
#####################################################################################

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_ROSTER_NS, XMPP_VCARD_NS

__all__ = ['RosterDispatcher']

class RosterDispatcher(component):
    
    Inboxes = {"inbox"              : "bridge.Element instance",
               "control"            : "Shutdown the client stream",
               "forward"            : "headstock.api.contact.Roster instance to be sent back to the client. Transforms the instance to a bridge.Element instance and puts it into the 'outbox'",}
    
    Outboxes = {"outbox"            : "bridge.Element instance",
                "signal"            : "Shutdown signal",
                "log"               : "log",
                "unknown"           : "Unknown element that could not be dispatched properly",
                "xmpp.result"       : "Query element in response to a query get/set in the roster namespace",
                "xmpp.get"          : "Get roster list from the server",
                "xmpp.set"          : "Set the roster list on the server",
                }
    
    def __init__(self):
       super(RosterDispatcher, self).__init__() 

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("forward"):
                r = self.recv("forward")
                self.send(Roster.to_element(r), "outbox")

            if self.dataReady("inbox"):
                e = self.recv("inbox")
                self.send(('INCOMING', e.xml_parent), "log")
                roster_type = e.xml_parent.get_attribute(u'type')
                handled = False
                if roster_type:
                    key = 'xmpp.%s' % roster_type
                    if key in self.outboxes:
                        self.send(Roster.from_element(e), key)
                        handled = True

                if not handled:
                    self.send(e, "unknown")

            if not self.anyReady():
                self.pause()
  
            yield 1
