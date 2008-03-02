# -*- coding: utf-8 -*-

from Kamaelia.Chassis.Graphline import Graphline
from Kamaelia.Chassis.Pipeline import Pipeline
from Kamaelia.Util.Backplane import Backplane
from Kamaelia.Util.Backplane import PublishTo, SubscribeTo
from Kamaelia.Internet.TCPClient import TCPClient
    
from headstock.protocol.core.stream import ClientStream, StreamError, SaslError
from headstock.protocol.core.presence import PresenceDispatcher, PresenceSubscriber
from headstock.protocol.core.roster import RosterDispatcher
from headstock.protocol.core.message import MessageDispatcher, MessageEchoer
from headstock.protocol.core.jid import JID
from headstock.lib.parser import XMLIncrParser
from headstock.lib.logger import Logger

from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS

def password_lookup(jid):
    return u"test"

def subscription_requested(p):
    # If you don't accept the subscription request, simply return None
    # otherwise returns "p"

    # Note that you could for instance call your database, or ask the
    # user, etc.
    print "# %s wants to subscribe to you. Enter 'yes' to allow, 'no' otherwise" % str(p.from_jid)
    allow = raw_input(">>> ")
    if allow == 'yes':
        p.swap_jids()
        return p

def setup(mh):
    jid = JID(u'test', u'sylvain-laptop', u'headstock')

    Backplane("LOGGER").activate()

    Pipeline(SubscribeTo("LOGGER"),
             Logger("./test4.log", True)
             ).activate()

    return Graphline(logger = PublishTo("LOGGER"),
                     tcp = TCPClient("localhost", 5222),
                     xmlparser = XMLIncrParser(),
                     xmpp = ClientStream(jid, password_lookup),
                     streamerr = StreamError(),
                     saslerr = SaslError(),
                     presence = Graphline(dispatcher = PresenceDispatcher(),
                                          logger = PublishTo("LOGGER"),
                                          sub = PresenceSubscriber(subscription_requested),
                                          linkages = {('', 'inbox'): ('dispatcher', 'inbox'),
                                                      ("dispatcher", "log"): ("logger", "inbox"),
                                                      ("dispatcher", "xmpp.subscribe"): ("sub", "inbox"),
                                                      ("sub", "outbox"): ("", "outbox")}),
                     roster = Graphline(dispatcher = RosterDispatcher(),
                                        logger = PublishTo("LOGGER"),
                                        linkages = {('', 'inbox'): ('dispatcher', 'inbox'),
                                                    ("dispatcher", "log"): ("logger", "inbox"),}),
                     message = Graphline(dispatcher = MessageDispatcher(),
                                         msg_handler = mh,
                                         logger = PublishTo("LOGGER"),
                                         linkages = {('', 'inbox'): ('dispatcher', 'inbox'),
                                                     ("dispatcher", "log"): ("logger", "inbox"),
                                                     ("dispatcher", "xmpp.chat"): ('msg_handler', 'inbox'),}),
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
                     )

    

def run(graph):
    graph.run()

def activate(graph):
    graph.activate()
    
if __name__ == '__main__':
    run(setup(MessageEchoer()))
