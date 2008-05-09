# -*- coding: utf-8 -*-
from Axon.Component import component
from Kamaelia.Chassis.Graphline import Graphline
from Kamaelia.Chassis.Pipeline import Pipeline
from Kamaelia.Util.Backplane import Backplane
from Kamaelia.Util.Backplane import PublishTo, SubscribeTo
from Kamaelia.Internet.TCPClient import TCPClient
from Kamaelia.Util.Console import ConsoleReader
from Axon.Ipc import shutdownMicroprocess, producerFinished
    
from headstock.protocol.core.stream import ClientStream, StreamError, SaslError
from headstock.protocol.core.presence import PresenceDispatcher, PresenceSubscriber
from headstock.protocol.core.roster import RosterDispatcher, RosterNull
from headstock.protocol.core.message import MessageDispatcher, MessageEchoer
from headstock.protocol.extension.activity import ActivityDispatcher
from headstock.protocol.extension.discovery import DiscoveryDispatcher
from headstock.protocol.extension.discovery import FeaturesDiscovery
from headstock.protocol.core.jid import JID
from headstock.lib.parser import XMLIncrParser
from headstock.lib.logger import Logger
from headstock.api.im import Message, Body, Event
from headstock.api.contact import Presence
from headstock.api.activity import Activity
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS, \
    XMPP_LAST_NS, XMPP_DISCO_INFO_NS

__all__ = ['Client']

class RosterHandler(component):    
    Inboxes = {"inbox"        : "headstock.api.contact.Roster instance",
               "control"      : "stops the component",
               "jid"          : "headstock.api.jid.JID instance received from the server",
               "ask-activity" : "request activity status to the server for each roster contact"}
    
    Outboxes = {"outbox"      : "UNUSED",
                "signal"      : "Shutdown signal",
                "message"     : "Message to send",
                "activity"    : "headstock.api.activity.Activity instance to send to the server"}

    def __init__(self, from_jid):
        super(RosterHandler, self).__init__() 
        self.from_jid = from_jid
        self.roster = None

    def initComponents(self):
        # We subscribe to the JID backplane component
        # that will inform us when the server has
        # returned the per-session jid
        sub = SubscribeTo("JID")
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')
            
            if self.dataReady("inbox"):
                roster = self.recv("inbox")
                self.roster = roster
                print "Your contacts:"
                for nodeid in roster.items:
                    contact = roster.items[nodeid]
                    print "  ", contact.jid
                    
            if self.dataReady('ask-activity'):
                self.recv('ask-activity')
                if self.roster:
                    for nodeid in self.roster.items:
                        contact = roster.items[nodeid]
                        a = Activity(unicode(self.from_jid), unicode(contact.jid))
                        self.send(a, 'activity')

            if not self.anyReady():
                self.pause()
  
            yield 1

class DummyMessageHandler(component):
    Inboxes = {"inbox"    : "headstock.api.contact.Message instance received from a peer"\
                   "or the string input in the console",
               "control"  : "stops the component"}
    
    Outboxes = {"outbox"  : "headstock.api.im.Message to send to the client",
                "signal"  : "Shutdown signal"}

    def __init__(self):
        super(DummyMessageHandler, self).__init__() 
        self.from_jid = None

    def initComponents(self):
        sub = SubscribeTo("JID")
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        sub = SubscribeTo("CONSOLE")
        self.link((sub, 'outbox'), (self, 'inbox'))
        self.addChildren(sub)
        sub.activate()

        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')
            
            if self.dataReady("inbox"):
                m = self.recv("inbox")
                # in this first case, we want to send the message
                # typed in the console.
                # The message is of the form:
                #    contant_jid message
                if isinstance(m, str) and m != '':
                    try:
                        contact_jid, message = m.split(' ', 1)
                    except ValueError:
                        print "Messages format: contact_jid message"
                        continue
                    m = Message(unicode(self.from_jid), unicode(contact_jid), 
                                type=u'chat', stanza_id=generate_unique())
                    m.event = Event.composing # note the composing event status
                    m.bodies.append(Body(unicode(message)))
                    self.send(m, "outbox")
                    
                    # Right after we sent the first message
                    # we send another one reseting the event status
                    m = Message(unicode(self.from_jid), unicode(contact_jid), 
                                type=u'chat', stanza_id=generate_unique())
                    self.send(m, "outbox")
                # In this case we actually received a message
                # from a contact, we print it.
                elif isinstance(m, Message):
                    for body in m.bodies:
                        print m.from_jid, ": ", str(body)

            if not self.anyReady():
                self.pause()
  
            yield 1

class DiscoHandler(component):
    Inboxes = {"inbox"          : "UNUSED",
               "control"        : "stops the component", 
               "initiate"       : "event informing the component the client session is active",
               "jid"            : "headstock.api.jid.JID instance received from the server",
               "features.result": "headstock.api.discovery.FeaturesDiscovery instance from the server",}
    
    Outboxes = {"outbox"           : "UNUSED",
                "signal"           : "Shutdown signal",
                "features-disco"   : "headstock.api.discovery.FeaturesDiscovery query to the server",  
                "features-announce": "headstock.api.discovery.FeaturesDiscovery informs"\
                    "the other components about the features instance received from the server"}

    def __init__(self, from_jid, to_jid):
        super(DiscoHandler, self).__init__() 
        self.from_jid = from_jid
        self.to_jid = to_jid

    def initComponents(self):
        sub = SubscribeTo("JID")
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        pub = PublishTo("DISCO_FEAT")
        self.link((self, 'features-announce'), (pub, 'inbox'))
        self.addChildren(sub)
        sub.activate()

        sub = SubscribeTo("BOUND")
        self.link((sub, 'outbox'), (self, 'initiate'))
        self.addChildren(sub)
        sub.activate()

        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')
            
            # When this box has some data, it means
            # that the client is bound to the server
            # Let's ask for its supported features then.
            if self.dataReady("initiate"):
                self.recv("initiate")
                d = FeaturesDiscovery(unicode(self.from_jid), self.to_jid)
                self.send(d, "features-disco")

            # The response to our discovery query
            # is a a headstock.api.discovery.FeaturesDiscovery instance.
            # What we immediatly do is to notify all handlers
            # interested in that event about it.
            if self.dataReady('features.result'):
                disco = self.recv('features.result')
                print "Supported features:"
                for feature in disco.features:
                    print "  ", feature.var
                self.send(disco, 'features-announce')

            if not self.anyReady():
                self.pause()
  
            yield 1

class ActivityHandler(component):
    Inboxes = {"inbox"   : "headstock.api.discovery.FeaturesDiscovery instance",
               "control" : "stops the component",
               }
    
    Outboxes = {"outbox"            : "UNUSED",
                "signal"            : "Shutdown signal",
                "activity-supported": "when used this tells the RosterHandler it needs"\
                    "to request the server for each contact's activity."\
                    "This is only used when the server supports the feature",
                }

    def __init__(self):
        super(ActivityHandler, self).__init__() 

    def initComponents(self):
        sub = SubscribeTo("DISCO_FEAT")
        self.link((sub, 'outbox'), (self, 'inbox'))
        self.addChildren(sub)
        sub.activate()
        
        return 1

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                disco = self.recv("inbox")
                support = disco.has_feature(XMPP_LAST_NS)
                print "Activity support: ", support
                if support:
                    self.send('', "activity-supported")

            if not self.anyReady():
                self.pause()
  
            yield 1

class Client(component):
    Inboxes = {"inbox"    : "",
               "jid": "",
               "control"  : "Shutdown the client stream",
               }
    
    Outboxes = {"outbox"  : "",
                "forward" : "",
                "log"     : "",
                "signal"  : "Shutdown signal",
                }

    def __init__(self, username, password, domain, resource=u"headstock-client1", 
                 server=u'localhost', port=5222, usetls=False):
        super(Client, self).__init__() 
        self.jid = JID(username, domain, resource)
        self.password = password
        self.server = server
        self.port = port
        self.client = None
        self.graph = None
        self.domain = domain
        self.usetls = usetls

    def passwordLookup(self, jid):
        return self.password

    def subscription_requested(self, p):
        # If you don't accept the subscription request, simply return None
        # otherwise returns "p"

        # Note that you could for instance call your database, or ask the
        # user, etc.
        print "# %s wants to subscribe to you. Enter 'yes' to allow, 'no' otherwise" % str(p.from_jid)
        allow = raw_input(">>> ")
        if allow == 'yes':
            p.swap_jids()
            return p

    def shutdown(self):
        p = Presence(self.jid)
        p.subscription = u'unavailable'
        self.send(Presence.to_element(p), 'forward')
        self.send('OUTGOING : </stream:stream>', 'log')
        self.send('</stream:stream>', 'outbox') 

    def setup(self):
        Backplane("LOGGER").activate()
        Backplane("CONSOLE").activate()
        Backplane("JID").activate()
        Backplane("BOUND").activate()
        Backplane("DISCO_FEAT").activate()

        sub = SubscribeTo("JID")
        sub.activate()
        self.link((sub, 'outbox'), (self, 'jid'))

        Pipeline(ConsoleReader(), PublishTo('CONSOLE')).activate()
        Pipeline(SubscribeTo("LOGGER"), Logger(path=None, stdout=True)).activate()

        ClientStream.Outboxes["%s.query" % XMPP_LAST_NS] = "Activity"
        ClientStream.Outboxes["%s.query" % XMPP_DISCO_INFO_NS] = "Discovery"
        self.client = ClientStream(self.jid, self.passwordLookup, use_tls=self.usetls)
        
        self.graph = Graphline(client = self,
                               console = SubscribeTo('CONSOLE'),
                               logger = PublishTo("LOGGER"),
                               tcp = TCPClient(self.server, self.port),
                               xmlparser = XMLIncrParser(),
                               xmpp = self.client,
                               streamerr = StreamError(),
                               saslerr = SaslError(),
                               discohandler = DiscoHandler(self.jid, self.domain),
                               activityhandler=ActivityHandler(),
                               rosterhandler = RosterHandler(self.jid),
                               msgdummyhandler = DummyMessageHandler(),
                               presencedisp = PresenceDispatcher(),
                               presencesub = PresenceSubscriber(self.subscription_requested),
                               rosterdisp = RosterDispatcher(),
                               msgdisp = MessageDispatcher(),
                               discodisp = DiscoveryDispatcher(),
                               activitydisp = ActivityDispatcher(),
                               pjid = PublishTo("JID"),
                               pbound = PublishTo("BOUND"),

                               linkages = {('xmpp', 'terminated'): ('client', 'inbox'),
                                           ('console', 'outbox'): ('client', 'control'),
                                           ('client', 'forward'): ('xmpp', 'forward'),
                                           ('client', 'outbox'): ('tcp', 'inbox'),
                                           ('client', 'signal'): ('tcp', 'control'),
                                           ("tcp", "outbox") : ("xmlparser", "inbox"),
                                           ("xmpp", "starttls") : ("tcp", "makessl"),
                                           ("tcp", "sslready") : ("xmpp", "tlssuccess"), 
                                           ("xmlparser", "outbox") : ("xmpp" , "inbox"),
                                           ("xmpp", "outbox") : ("tcp" , "inbox"),
                                           ("xmpp", "reset"): ("xmlparser", "reset"),
                                           ("client", "log"): ("logger", "inbox"),
                                           ("xmpp", "log"): ("logger", "inbox"),
                                           ("xmpp", "jid"): ("pjid", "inbox"),
                                           ("xmpp", "bound"): ("pbound", "inbox"),

                                           # Presence 
                                           ("xmpp", "%s.presence" % XMPP_CLIENT_NS): ("presencedisp", "inbox"),
                                           ("presencedisp", "log"): ('logger', "inbox"),
                                           ("presencedisp", "xmpp.subscribe"): ("presencesub", "inbox"),
                                           ("presencesub", "outbox"): ("xmpp", "forward"),

                                           # Roster
                                           ("xmpp", "%s.query" % XMPP_ROSTER_NS): ("rosterdisp", "inbox"),
                                           ("rosterdisp", "log"): ('logger', "inbox"),
                                           ('rosterdisp', 'xmpp.result'): ('rosterhandler', 'inbox'),

                                           # Discovery
                                           ("xmpp", "%s.query" % XMPP_DISCO_INFO_NS): ("discodisp", "features.inbox"),
                                           ("discodisp", "log"): ('logger', "inbox"),
                                           ("discohandler", "features-disco"): ('discodisp', "features.forward"),
                                           ("discodisp", "out.features.result"): ('discohandler', "features.result"),
                                           ("discodisp", "outbox"): ("xmpp", "forward"),

                                           # Message
                                           ("xmpp", "%s.message" % XMPP_CLIENT_NS): ("msgdisp", "inbox"),
                                           ("msgdisp", "log"): ('logger', "inbox"),
                                           ("msgdisp", "xmpp.chat"): ('msgdummyhandler', 'inbox'),
                                           ("msgdummyhandler", "outbox"): ('msgdisp', 'forward'),
                                           ("msgdisp", "outbox"): ("xmpp", "forward"),

                                           # Activity
                                           ("xmpp", "%s.query" % XMPP_LAST_NS): ("activitydisp", "inbox"),
                                           ("activitydisp", "log"): ('logger', "inbox"),
                                           ("activitydisp", "outbox"): ("xmpp", "forward"),
                                           ("activityhandler", 'activity-supported'): ('rosterhandler', 'ask-activity'),
                                           ("rosterhandler", 'activity'): ('activitydisp', 'forward'),
                                           }
                               )
        self.addChildren(self.graph)
        self.graph.activate()

        return 1

    def main(self):
        yield self.setup()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")

                if isinstance(mes, str):
                    if mes.strip() == 'quit':
                        self.shutdown()
                elif isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(mes, "signal")
                    break

            if self.dataReady("inbox"):
                msg = self.recv('inbox')
                if msg == "quit":
                    self.send(shutdownMicroprocess(), "signal")
                    yield 1
                    break

            if self.dataReady("jid"):
                self.jid = self.recv('jid')
                
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield 1
        self.stop()
        print "You can hit Ctrl-C to shutdown all processes now." 

if __name__ == '__main__':
    
    def parse_commandline():
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-d", "--xmpp-domain", dest="domain",
                          help="XMPP server domain")
        parser.set_defaults(domain='localhost')
        parser.add_option("-a", "--address", dest="address", action="store",
                           help="XMPP server address")
        parser.set_defaults(address='localhost:5222')
        parser.add_option("-u", "--username", dest="username",
                          help="XMPP username", action="store")
        parser.add_option("-p", "--password", action="store", dest="password",
                          help="XMPP password")
        parser.add_option("-t", "--usetls", dest="usetls", action="store_true",
                           help="Use TLS")
        parser.set_defaults(usetls=False)
        (options, args) = parser.parse_args()

        return options

    def run():
        options = parse_commandline()
        host, port = options.address.split(':')
        client = Client(unicode(options.username), 
                        unicode(options.password), 
                        unicode(options.domain),
                        server=host, port=int(port),
                        usetls=options.usetls)
        client.run()

    run()
