# -*- coding: utf-8 -*-

from Kamaelia.Chassis.Graphline import Graphline
from Kamaelia.Chassis.Pipeline import Pipeline
from Kamaelia.Util.Backplane import Backplane
from Kamaelia.Util.Backplane import PublishTo, SubscribeTo
from Kamaelia.Internet.TCPClient import TCPClient
    
from headstock.protocol.core.stream import ClientStream, StreamError, SaslError
from headstock.protocol.core.presence import PresenceDispatcher
from headstock.protocol.core.roster import RosterDispatcher
from headstock.protocol.core.message import MessageDispatcher
from headstock.protocol.core.jid import JID
from headstock.lib.parser import XMLIncrParser
from headstock.lib.logger import Logger

from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS

def password_lookup(jid):
    return u"test"

def run():
    jid = JID(u'test', u'localhost', u'headstock')

    Backplane("LOGGER").activate()

    Pipeline(SubscribeTo("LOGGER"),
             Logger("./test4.log", True)
             ).activate()

    Graphline(logger = PublishTo("LOGGER"),
              tcp = TCPClient("localhost", 5222),
              xmlparser = XMLIncrParser(),
              xmpp = ClientStream(jid, password_lookup),
              streamerr = StreamError(),
              saslerr = SaslError(),
              presence = Graphline(dispatcher = PresenceDispatcher(),
                                   linkages = {('', 'inbox'): ('dispatcher', 'inbox'),}),
              roster = Graphline(dispatcher = RosterDispatcher(),
                                 linkages = {('', 'inbox'): ('dispatcher', 'inbox'),}),
              message = Graphline(dispatcher = MessageDispatcher(),
                                  linkages = {('', 'inbox'): ('dispatcher', 'inbox'),}),
              linkages = {("tcp", "outbox") : ("xmlparser", "inbox"),
                          ("xmlparser", "outbox") : ("xmpp" , "inbox"),
                          ("xmpp", "outbox") : ("tcp" , "inbox"),
                          ("xmpp", "reset"): ("xmlparser", "reset"),
                          ("xmpp", "log"): ("logger", "inbox"),
                          ("xmpp", "%s.presence" % XMPP_CLIENT_NS): ("presence", "inbox"),
                          ("presence", "outbox"): ("xmpp", "forward"),
                          ("xmpp", "%s.query" % XMPP_ROSTER_NS): ("roster", "inbox"),
                          ("message", "outbox"): ("xmpp", "forward"),
                          ("xmpp", "%s.message" % XMPP_CLIENT_NS): ("message", "inbox"),
                          ("roster", "outbox"): ("xmpp", "forward"),
                          ("xmpp", "error"): ("streamerr", "inbox"),
                          ("xmpp", "error"): ("saslerr", "inbox"),}
              ).run()

    
if __name__ == '__main__':
    run()
