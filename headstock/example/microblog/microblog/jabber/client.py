# -*- coding: utf-8 -*-
"""
This module is a simple XMPP chat client demonstrating the use of headstock.
Many Kamaelia components are created to manage different XMPP kind of stanzas.

* RosterHandler:
  * querying the server for the roster list
  * if supported by server, asking for the last activity of each contact

* DummyMessageHandler:
  * sending a message typed into the console window
  * printing to the console any received messages

* DiscoHandler: 
  * querying for the supported features by the server
  * dispatching the result of the previous query to components interested in that event

* ActivityHandler:
  * dispatching to the RosterHandler the fact the server supports the feature

* RegisterHandler:
  * registring a new user using in-band registration if supported

The actual XMPP client is the Client component that sets up the different
dispatchers and handlers involved by liking each inbox to the expected outbox and
vcie versa.

"""
from Axon.Ipc import *
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished
from Kamaelia.Chassis.Graphline import Graphline
from Kamaelia.Chassis.Pipeline import Pipeline
from Kamaelia.Util.Backplane import Backplane
from Kamaelia.Util.Backplane import PublishTo, SubscribeTo
from Kamaelia.Internet.TCPClient import TCPClient
from Kamaelia.Protocol.HTTP.HTTPClient import SimpleHTTPClient
    
from headstock.protocol.core.stream import ClientStream, StreamError, SaslError
from headstock.protocol.core.presence import PresenceDispatcher
from headstock.protocol.core.roster import RosterDispatcher, RosterNull
from headstock.protocol.core.message import MessageDispatcher, MessageEchoer
from headstock.protocol.extension.register import RegisterDispatcher
from headstock.protocol.extension.activity import ActivityDispatcher
from headstock.protocol.extension.discovery import DiscoveryDispatcher
from headstock.protocol.extension.discovery import FeaturesDiscovery
from headstock.protocol.extension.pubsub import *
from headstock.api import Entity
from headstock.api.jid import JID
from headstock.api.im import Message, Body, Event, XHTMLBody
from headstock.api.contact import Presence, Roster, Item
from headstock.api.activity import Activity
from headstock.api.registration import Registration
from headstock.lib.parser import XMLIncrParser
from headstock.lib.logger import Logger
from headstock.lib.utils import generate_unique, remove_BOM

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS, \
    XMPP_LAST_NS, XMPP_DISCO_INFO_NS, XMPP_IBR_NS, \
    XMPP_DISCO_ITEMS_NS, XMPP_PUBSUB_NS, XMPP_PUBSUB_EVENT_NS,\
    XMPP_PUBSUB_OWNER_NS

from microblog.jabber.pubsub import DiscoHandler, ItemsHandler, MessageHandler

__all__ = ['Client']

class RosterHandler(component):    
    Inboxes = {"inbox"        : "headstock.api.contact.Roster instance",
               "control"      : "stops the component",
               "pushed"       : "roster stanzas pushed by the server",
               "jid"          : "headstock.api.jid.JID instance received from the server",
               "ask-activity" : "request activity status to the server for each roster contact"}
    
    Outboxes = {"outbox"      : "UNUSED",
                "signal"      : "Shutdown signal",
                "message"     : "Message to send",
                "result"      : "", 
                'roster-updated': "",
                "activity"    : "headstock.api.activity.Activity instance to send to the server"}

    def __init__(self, from_jid, session_id):
        super(RosterHandler, self).__init__() 
        self.from_jid = from_jid
        self.roster = None
        self.session_id = session_id

    def initComponents(self):
        # We subscribe to the JID backplane component
        # that will inform us when the server has
        # returned the per-session jid
        sub = SubscribeTo("JID.%s" % self.session_id)
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
            
            if self.dataReady("pushed"):
                roster = self.recv('pushed')
                for nodeid in roster.items:
                    self.send(Roster(from_jid=self.from_jid, to_jid=nodeid,
                                     type=u'result', stanza_id=generate_unique()), 'result')
                
            if self.dataReady("inbox"):
                roster = self.recv("inbox")
                self.roster = roster
                for nodeid in roster.items:
                    contact = roster.items[nodeid]

                self.send(roster, 'roster-updated')
                    
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
               "jid"      : "headstock.api.jid.JID instance received from the server",
               "roster-received": "",
               "control"  : "stops the component"}
    
    Outboxes = {"outbox"  : "headstock.api.im.Message to send to the client",
                "signal"  : "Shutdown signal",
                "PI"      : "Publish item",
                "GEO"     : "Publish item with heo coordinates",
                "DI"      : "Retract item",
                "PN"      : "Purge node from items",
                "CN"      : "Create node",
                "DN"      : "Delete node",
                "CCN"     : "Create collection node",
                "DCN"     : "Delete collection node",
                "SN"      : "Subscribe to node",
                "UN"      : "Unsubscribe from node"}

    def __init__(self, session_id, profile):
        super(DummyMessageHandler, self).__init__() 
        self.from_jid = None
        self.session_id = session_id
        self.profile = profile

        self.roster = None

    def initComponents(self):
        sub = SubscribeTo("JID.%s" % self.session_id)
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
            
            if self.dataReady("roster-received"):
                self.roster = self.recv("roster-received")
                
            if self.dataReady("inbox"):
                m = self.recv("inbox")
                if isinstance(m, str) and m != '':
                    pass
                # In this case we actually received a message
                # from a contact, we print it.
                elif isinstance(m, Message):
                    for body in m.bodies:
                        message = remove_BOM(body.plain_body).strip()
                        print "Received message: %s" % repr(message)
                        try:
                            action, data = message.split(' ', 1)
                        except ValueError:
                            action = 'PI'
                            data = message
                            
                        if action in self.outboxes:
                            self.send(data, action)

                        if self.roster:
                            for nodeid in self.roster.items:
                                m = Message(unicode(self.from_jid), unicode(nodeid),
                                            type=u'chat', stanza_id=generate_unique())
                                m.event = Event.composing 
                                m.bodies.append(Body(unicode(data)))
                                self.send(m, "outbox")

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

    def __init__(self, session_id):
        super(ActivityHandler, self).__init__() 
        self.session_id = session_id

    def initComponents(self):
        sub = SubscribeTo("DISCO_FEAT.%s" % self.session_id)
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

            if self.dataReady("inbox"):
                disco = self.recv("inbox")
                support = disco.has_feature(XMPP_LAST_NS)
                if support:
                    self.send('', "activity-supported")

            if not self.anyReady():
                self.pause()
  
            yield 1

class PresenceHandler(component):
    Inboxes = {"inbox"       : "headstock.api.contact.Presence instance",
               "control"     : "Shutdown the client stream",
               "jid"      : "headstock.api.jid.JID instance received from the server",
               "subscribe"   : "",
               "unsubscribe" : "",}
    
    Outboxes = {"outbox" : "headstock.api.contact.Presence instance to return to the server",
                "signal" : "Shutdown signal",
                "roster" : "",
                "log"    : "log",}
    
    def __init__(self, session_id):
        super(PresenceHandler, self).__init__()
        self.session_id = session_id

    def initComponents(self):
        sub = SubscribeTo("JID.%s" % self.session_id)
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

                #if '.microblogging' in unicode(self.from_jid):
                #    sibling = JID(unicode('%s.microblogging' % self.from_jid.node),
                #                  self.from_jid.domain)
                #    p = Presence(from_jid=self.from_jid, to_jid=unicode(sibling),
                #                 type=u'subscribe')
                #    self.send(p, "outbox")

            if self.dataReady("subscribe"):
                p = self.recv("subscribe")
                p.swap_jids()

                # Automatically accept any subscription requests
                p = Presence(from_jid=p.from_jid, to_jid=unicode(p.to_jid),
                             type=u'subscribed')
                self.send(p, "outbox")
                
                # Automatically subscribe in return as well
                p = Presence(from_jid=p.from_jid, to_jid=unicode(p.to_jid),
                             type=u'subscribe')
                self.send(p, "outbox")
                
            if self.dataReady("unsubscribe"):
                p = self.recv("unsubscribe")
                p.swap_jids()
                
                # We stop our subscription to the other user
                p = Presence(from_jid=p.from_jid, to_jid=unicode(p.to_jid),
                             type=u'unsubscribed')
                self.send(p, "outbox")
                
                # We stop the other user's subscription
                p = Presence(from_jid=p.from_jid, to_jid=unicode(p.to_jid),
                             type=u'unsubscribe')
                self.send(p, "outbox")

                # We remove this user from our roster list
                r = Roster(from_jid=p.from_jid, type=u'set')
                i = Item(p.to_jid)
                i.subscription = u'remove'
                r.items[unicode(p.to_jid)] = i
                self.send(r, 'roster')

                # We tell the other user we're not available anymore
                p = Presence(from_jid=p.from_jid, to_jid=unicode(p.to_jid),
                             type=u'unavailable')
                self.send(p, "outbox")
                
            if not self.anyReady():
                self.pause()
  
            yield 1
    

class RegistrationHandler(component):
    Inboxes = {"inbox"   : "headstock.api.registration.Registration",
               "error"   : "headstock.api.registration.Registration",
               "control" : "Shutdown the client stream",
               "_response": ""}
    
    Outboxes = {"outbox" : "headstock.api.registration.Registration",
                "signal" : "Shutdown signal",
                "log"    : "log",
               "_request": ""}
    
    def __init__(self, username, password, session_id, profile):
        super(RegistrationHandler, self).__init__()
        self.username = username
        self.password = password
        self.profile = profile
        self.registration_id = None
        self.session_id = session_id

    def initComponents(self):
        self.client = SimpleHTTPClient()
        self.addChildren(self.client)
        self.link((self, '_request'), (self.client, 'inbox')) 
        self.link((self.client, 'outbox'), (self, '_response')) 
        self.client.activate()

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("_response"):
                self.recv("_response")
                
            if self.dataReady("inbox"):
                r = self.recv('inbox')
                if r.registered:
                    self.send("'%s' is already a registered username." % r.infos[u'username'], 'log')
                    c = Client.Sessions[r.infos[u'username']]
                    c.shutdown()
                    del Client.Sessions[r.infos[u'username']]
                elif self.registration_id == r.stanza_id:
                    c = Client.Sessions[r.infos[u'username']]
                    c.shutdown()
                    del Client.Sessions[r.infos[u'username']]

                    if '.microblogging' not in r.infos[u'username']:
                        body = self.profile.xml()
                        params = {'url': 'http://localhost:8080/profile/',
                                  'method': 'POST', 'postbody': body, 
                                  'extraheaders': {'content-type': 'application/xml',
                                                   'slug': self.profile.username,
                                                   'content-length': len(body)}}
                        self.send(params, '_request') 
                else:
                    if 'username' in r.infos and 'password' in r.infos:
                        self.registration_id = generate_unique()
                        r = Registration(type=u'set', stanza_id=self.registration_id)
                        r.infos[u'username'] = self.username
                        r.infos[u'password'] = self.password
                        self.send(r, 'outbox')
                
            if self.dataReady("error"):
                r = self.recv('error')
                if r.error.code == '409':
                    self.send("'%s' is already a registered username." % r.infos[u'username'], 'log')
                    c = Client.Sessions[r.infos[u'username']]
                    c.shutdown()
                    del Client.Sessions[r.infos[u'username']]
                self.send(r.error, 'log')

            if not self.anyReady():
                self.pause()
  
            yield 1

class Client(component):
    Inboxes = {"inbox"      : "",
               "jid"        : "",
               "streamfeat" : "",
               "connected"  : "",
               "unhandled"  : "",
               "control"    : "Shutdown the client stream"}
    
    Outboxes = {"outbox"  : "",
                "forward" : "",
                "log"     : "",
                "doauth"  : "",
                "signal"  : "Shutdown signal",
                "doregistration" : ""}

    Domain = None
    Host = u'localhost'
    Port = 5222

    Sessions = {}

    def __init__(self, atompub, username, password, domain, resource=u"headstock-client1", 
                 server=u'localhost', port=5222, usetls=False, register=False, session_id=None, profile=None):
        super(Client, self).__init__() 
        self.running = False
        self.connected = False
        self.atompub = atompub
        if not session_id:
            session_id = generate_unique()
        self.session_id = session_id
        self.backplanes = []
        self.username = username
        self.password = password
        self.jid = JID(self.username, domain, '%s!%s' % (resource, session_id))
        self.server = server
        self.port = port
        self.client = None
        self.graph = None
        self.domain = domain
        self.usetls = usetls
        self.register = register
        self.restartable = False
        self.profile = profile

    @staticmethod
    def start_clients(atompub, users):
        for username, password in users:
            profile = atompub.load_profile(username)
            Client.connect_jabber_user(atompub, username, password, profile)

    @staticmethod
    def register_jabber_user(atompub, username, password, profile):
        c = Client(atompub, unicode(username), unicode(password), 
                   domain=Client.Domain, server=Client.Host, port=Client.Port,
                   usetls=False, register=True, profile=profile)
        Client.Sessions[c.username] = c
        c.activate()

        username = unicode('%s.microblogging' % username)
        c = Client(atompub, unicode(username), unicode(password), 
                   domain=Client.Domain, server=Client.Host, port=Client.Port,
                   usetls=False, register=True, profile=profile)
        Client.Sessions[c.username] = c
        c.activate()

    @staticmethod
    def connect_jabber_user(atompub, username, password, profile):
        #c = Client(atompub, unicode(username), unicode(password), 
        #           domain=Client.Domain, server=Client.Host, port=Client.Port,
        #           usetls=True, register=False, profile=profile)
        #Client.Sessions[c.username] = c
        #c.activate()
        
        username = unicode('%s.microblogging' % username)
        c = Client(atompub, unicode(username), unicode(password), 
                   domain=Client.Domain, server=Client.Host, port=Client.Port,
                   usetls=False, register=False, profile=profile)
        Client.Sessions[c.username] = c
        c.activate()

    @staticmethod
    def disconnect_jabber_user(username):
        if username in Client.Sessions:
            c = Client.Sessions[username]
            del Client.Sessions[username]
            c.shutdown()

    @staticmethod
    def get_status(username):
        return username in Client.Sessions

    @staticmethod
    def is_registered(username):
        if username.lower() in Client.Sessions:
            return Client.Sessions[username.lower()]

        return False

    def passwordLookup(self, jid):
        return self.password

    def shutdown(self):
        #self.send(Presence.to_element(Presence(self.jid, type=u'unavailable')), 'forward')
        self.send('OUTGOING : </stream:stream>', 'log')
        self.send('</stream:stream>', 'outbox')
        self.running = False 

    def abort(self):
        self.send('OUTGOING : </stream:stream>', 'log')
        self.send('</stream:stream>', 'outbox')
        self.running = False 

    def setup(self):
        self.running = True

        # Backplanes are like a global entry points that
        # can be accessible both for publishing and
        # recieving data. 
        # In other words, a component interested
        # in advertising to many other components that
        # something happened may link one of its outbox
        # to a PublishTo component's inbox.
        # A component wishing to receive that piece of
        # information will link one of its inbox
        # to the SubscribeTo component's outbox.
        # This helps greatly to make components more
        # loosely connected but also allows for some data
        # to be dispatched at once to many (such as when
        # the server returns the per-session JID that
        # is of interest for most other components).
        self.backplanes.append(Backplane("JID.%s" % self.session_id).activate())
        # Used to inform components that the session is now active
        self.backplanes.append(Backplane("BOUND.%s" % self.session_id).activate())
        # Used to inform components of the supported features
        self.backplanes.append(Backplane("DISCO_FEAT.%s" % self.session_id).activate())

        sub = SubscribeTo("JID.%s" % self.session_id)
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        sub = SubscribeTo("BOUND.%s" % self.session_id)
        self.link((sub, 'outbox'), (self, 'connected'))
        self.addChildren(sub)
        sub.activate()

        # Add two outboxes ro the ClientSteam to support specific extensions.
        ClientStream.Outboxes["%s.query" % XMPP_IBR_NS] = "Registration"
        ClientStream.Outboxes["%s.query" % XMPP_LAST_NS] = "Activity"
        ClientStream.Outboxes["%s.query" % XMPP_DISCO_INFO_NS] = "Discovery"
        ClientStream.Outboxes["%s.query" % XMPP_DISCO_ITEMS_NS] = "PubSub Discovery of Nodes"
        ClientStream.Outboxes["%s.subscribe" % XMPP_PUBSUB_NS] = "Pubsub subscription handler"
        ClientStream.Outboxes["%s.unsubscribe" % XMPP_PUBSUB_NS] = "Pubsub unsubscription handler"
        ClientStream.Outboxes["%s.subscriptions" % XMPP_PUBSUB_NS] = "Pubsub subscriptions handler"
        ClientStream.Outboxes["%s.affiliations" % XMPP_PUBSUB_NS] = "Pubsub affiliations handler"
        ClientStream.Outboxes["%s.create" % XMPP_PUBSUB_NS] = "Pubsub node creation handler"
        ClientStream.Outboxes["%s.purge" % XMPP_PUBSUB_OWNER_NS] = "Pubsub node purge handler"
        ClientStream.Outboxes["%s.delete" % XMPP_PUBSUB_OWNER_NS] = "Pubsub node delete handler"
        ClientStream.Outboxes["%s.publish" % XMPP_PUBSUB_NS] = "Pubsub item publication handler"
        ClientStream.Outboxes["%s.retract" % XMPP_PUBSUB_NS] = "Pubsub item deletion handler"
        ClientStream.Outboxes["%s.x" % XMPP_PUBSUB_EVENT_NS] = ""
        ClientStream.Outboxes["%s.event" % XMPP_PUBSUB_EVENT_NS] = ""

        self.client = ClientStream(self.jid, self.passwordLookup, use_tls=self.usetls)
        self.addChildren(self.client)
        self.client.activate()

        self.graph = Graphline(client = self,
                               logger = Logger(path='./logs/%s.log' % self.username, 
                                               stdout=True, name=self.session_id),
                               tcp = TCPClient(self.server, self.port),
                               xmlparser = XMLIncrParser(),
                               xmpp = self.client,
                               streamerr = StreamError(),
                               saslerr = SaslError(),
                               discohandler = DiscoHandler(self.jid, self.atompub, self.domain, 
                                                           session_id=self.session_id,
                                                           profile=self.profile),
                               activityhandler = ActivityHandler(session_id=self.session_id),
                               rosterhandler = RosterHandler(self.jid, session_id=self.session_id),
                               registerhandler = RegistrationHandler(self.username, self.password,
                                                                     self.session_id, profile=self.profile),
                               msgdummyhandler = DummyMessageHandler(session_id=self.session_id, 
                                                                     profile=self.profile),
                               presencehandler = PresenceHandler(session_id=self.session_id),
                               itemshandler = ItemsHandler(self.jid, self.atompub, self.domain,
                                                           session_id=self.session_id, 
                                                           profile=self.profile),
                               pubsubmsgeventhandler = MessageHandler(self.jid, self.atompub, self.domain,
                                                                      session_id=self.session_id,
                                                                      profile=self.profile),
                               presencedisp = PresenceDispatcher(),
                               rosterdisp = RosterDispatcher(),
                               msgdisp = MessageDispatcher(),
                               discodisp = DiscoveryDispatcher(),
                               activitydisp = ActivityDispatcher(),
                               registerdisp = RegisterDispatcher(),
                               pubsubdisp = PubSubDispatcher(),
                               pjid = PublishTo("JID.%s" % self.session_id),
                               pbound = PublishTo("BOUND.%s" % self.session_id),

                               linkages = {('xmpp', 'terminated'): ('client', 'inbox'),
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
                                           ("xmpp", "features"): ("client", "streamfeat"),
                                           ("xmpp", "unhandled"): ("client", "unhandled"),
                                           ("client", "doauth"): ("xmpp", "auth"),
                                           
                                           # Registration
                                           ("xmpp", "%s.query" % XMPP_IBR_NS): ("registerdisp", "inbox"),
                                           ("registerdisp", "log"): ('logger', "inbox"),
                                           ("registerdisp", "xmpp.error"): ("registerhandler", "error"),
                                           ("registerdisp", "xmpp.result"): ("registerhandler", "inbox"),
                                           ("registerhandler", "outbox"): ("registerdisp", "forward"),
                                           ("client", "doregistration"): ("registerdisp", "forward"),
                                           ("registerdisp", "outbox"): ("xmpp", "forward"),
                                           
                                           # Presence 
                                           ("xmpp", "%s.presence" % XMPP_CLIENT_NS): ("presencedisp", "inbox"),
                                           ("presencedisp", "log"): ('logger', "inbox"),
                                           ("presencedisp", "xmpp.subscribe"): ("presencehandler", "subscribe"),
                                           ("presencedisp", "xmpp.unsubscribe"): ("presencehandler", "unsubscribe"),
                                           ("presencehandler", "outbox"): ("presencedisp", "forward"),
                                           ("presencehandler", "roster"): ("rosterdisp", "forward"),
                                           ("presencedisp", "outbox"): ("xmpp", "forward"),

                                           # Roster
                                           ("xmpp", "%s.query" % XMPP_ROSTER_NS): ("rosterdisp", "inbox"),
                                           ("rosterdisp", "log"): ('logger', "inbox"),
                                           ('rosterdisp', 'xmpp.set'): ('rosterhandler', 'pushed'),
                                           ('rosterdisp', 'xmpp.result'): ('rosterhandler', 'inbox'),
                                           ('rosterhandler', 'result'): ('rosterdisp', 'forward'),
                                           ('rosterhandler', 'roster-updated'): ('msgdummyhandler', 'roster-received'),
                                           ("rosterdisp", "outbox"): ("xmpp", "forward"),

                                           # Discovery
                                           ("xmpp", "%s.query" % XMPP_DISCO_INFO_NS): ("discodisp", "features.inbox"),
                                           ("xmpp", "%s.query" % XMPP_DISCO_ITEMS_NS): ("discodisp", "items.inbox"),
                                           ("xmpp", "%s.affiliations" % XMPP_PUBSUB_NS): ("discodisp", "affiliation.inbox"),
                                           ("xmpp", "%s.subscriptions" % XMPP_PUBSUB_NS): ("discodisp", "subscription.inbox"),
                                           ("discodisp", "log"): ('logger', "inbox"),
                                           ("discohandler", "features-disco"): ('discodisp', "features.forward"),
                                           ('discohandler', 'items-disco'): ('discodisp', 'items.forward'),
                                           ('discohandler', 'subscriptions-disco'): ('discodisp', 'subscription.forward'),
                                           ('discohandler', 'affiliations-disco'): ('discodisp', 'affiliation.forward'),
                                           ("discodisp", "out.features.result"): ('discohandler', "features.result"),
                                           ("discodisp",'subscription.outbox'):('xmpp','forward'),
                                           ("discodisp",'affiliation.outbox'):('xmpp','forward'),
                                           ("discodisp",'out.subscription.result'): ('discohandler','subscriptions.result'),
                                           ("discodisp",'out.affiliation.result'): ('discohandler','affiliations.result'),
                                           ("discodisp", 'out.items.result'): ('discohandler', 'items.result'),
                                           ("discodisp", 'out.items.error'): ('discohandler', 'items.error'),
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

                                           # Pubsub
                                           ("xmpp", "%s.create" % XMPP_PUBSUB_NS): ("pubsubdisp", "create.inbox"),
                                           ("xmpp", "%s.delete" % XMPP_PUBSUB_OWNER_NS): ("pubsubdisp", "delete.inbox"),
                                           ("xmpp", "%s.purge" % XMPP_PUBSUB_OWNER_NS): ("pubsubdisp", "purge.inbox"),
                                           ("xmpp", "%s.subscribe" % XMPP_PUBSUB_NS): ("pubsubdisp", "subscribe.inbox"),
                                           ("xmpp", "%s.unsubscribe" % XMPP_PUBSUB_NS):("pubsubdisp", "unsubscribe.inbox"),
                                           ("xmpp", "%s.publish" % XMPP_PUBSUB_NS): ("pubsubdisp", "publish.inbox"),
                                           ("xmpp", "%s.retract" % XMPP_PUBSUB_NS): ("pubsubdisp", "retract.inbox"),
                                           ("xmpp", "%s.x" % XMPP_PUBSUB_EVENT_NS): ("pubsubdisp", "message.inbox"),
                                           ("xmpp", "%s.event" % XMPP_PUBSUB_EVENT_NS): ("pubsubdisp", "message.inbox"),
                                           ("pubsubdisp", "log"): ('logger', "inbox"),
                                           ("discohandler", "create-node"): ("pubsubdisp", "create.forward"),
                                           ("discohandler", "delete-node"): ("pubsubdisp", "delete.forward"),
                                           ("discohandler", "subscribe-node"): ("pubsubdisp", "subscribe.forward"),
                                           ("discohandler", "unsubscribe-node"): ("pubsubdisp", "unsubscribe.forward"),
                                           ("pubsubdisp", "create.outbox"): ("xmpp", "forward"),
                                           ("pubsubdisp", "delete.outbox"): ("xmpp", "forward"),
                                           ("pubsubdisp", "purge.outbox"): ("xmpp", "forward"),
                                           ("pubsubdisp", "subscribe.outbox"): ("xmpp", "forward"),
                                           ("pubsubdisp", "unsubscribe.outbox"): ("xmpp", "forward"),
                                           ("pubsubdisp", "publish.outbox"): ("xmpp", "forward"),
                                           ("pubsubdisp", "retract.outbox"): ("xmpp", "forward"),
                                           ("pubsubdisp", "out.create.result"): ("discohandler", "created"),
                                           ("pubsubdisp", "out.subscribe.result"): ("discohandler", "subscribed"),
                                           ("pubsubdisp", "out.delete.result"): ("discohandler", "deleted"),
                                           ("pubsubdisp", "out.create.error"): ("discohandler", "error"),
                                           ("pubsubdisp", "out.delete.error"): ("discohandler", "error"),
                                           ("pubsubdisp", "out.publish.error"): ("itemshandler", "publish.error"),
                                           ("pubsubdisp", "out.retract.error"): ("itemshandler", "retract.error"),
                                           ("pubsubdisp", "out.publish.result"): ("itemshandler", "published"),
                                           ("pubsubdisp", "out.message"): ('pubsubmsgeventhandler', 'inbox'),
                                           ('itemshandler', 'publish'): ('pubsubdisp', 'publish.forward'),
                                           ('itemshandler', 'delete'): ('pubsubdisp', 'retract.forward'),
                                           ('itemshandler', 'purge'): ('pubsubdisp', 'purge.forward'),
                                           ("msgdummyhandler", "PI"): ('itemshandler', 'topublish'),
                                           ("msgdummyhandler", "GEO"): ('itemshandler', 'topublish'),
                                           ("msgdummyhandler", "DI"): ('itemshandler', 'todelete'),
                                           ("msgdummyhandler", "PN"): ('itemshandler', 'topurge'),
                                           ("msgdummyhandler", "CN"): ('discohandler', 'docreate'),
                                           ("msgdummyhandler", "DN"): ('discohandler', 'dodelete'),
                                           ("msgdummyhandler", "SN"): ('discohandler', 'dosubscribe'),
                                           ("msgdummyhandler", "UN"): ('discohandler', 'dounsubscribe'),
                                           ('pubsubmsgeventhandler', 'items-disco'): ('discodisp', 'items.forward'),
                                           }
                               )

        self.addChildren(self.graph)
        self.graph.activate()

        return 1

    def main(self):
        yield self.setup()

        while self.running:
            if self.dataReady("control"):
                mes = self.recv("control")

                if isinstance(mes, str):
                    if mes.strip() == 'quit':
                        self.shutdown()
                elif isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(mes, "signal")
                    break

            if self.dataReady("connected"):
                self.recv('connected')
                self.connected = True
                    

            if self.dataReady("unhandled"):
                msg = self.recv('unhandled')
                self.send(('UNHANDLED', msg), 'log')
                
            if self.dataReady("inbox"):
                msg = self.recv('inbox')
                if msg == "quit":
                    self.send(shutdownMicroprocess(), "signal")
                    yield 1
                    break

            if self.dataReady("streamfeat"):
                feat = self.recv('streamfeat')
                if feat.register and self.register:
                    self.send(Registration(), 'doregistration')
                elif self.register and not feat.register:
                    print "The server does not support in-band registration. Closing connection."
                    self.abort()
                else:
                    self.send(feat, 'doauth')
                
            if self.dataReady("jid"):
                self.jid = self.recv('jid')
                
            if not self.anyReady():
                self.pause()
  
            yield 1

        yield shutdownMicroprocess(self, self.children, self.backplanes)
