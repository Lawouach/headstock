# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from Kamaelia.Chassis.Graphline import Graphline
from Kamaelia.Chassis.Pipeline import Pipeline
from Kamaelia.Util.Backplane import Backplane
from Kamaelia.Util.Backplane import PublishTo, SubscribeTo
from Kamaelia.Util.Fanout import Fanout
from Kamaelia.Util.OneShot import OneShot
from Kamaelia.Util.Console import ConsoleReader
from Kamaelia.Internet.TCPClient import TCPClient
  
from headstock.protocol.core.stream import ClientStream, StreamError, SaslError
from headstock.api.jid import JID
from headstock.api import Entity
from headstock.api.registration import Registration
from headstock.api.contact import Presence
from headstock.api.error import Error
from headstock.lib.parser import XMLIncrParser
from headstock.lib.logger import Logger
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS, \
    XMPP_LAST_NS, XMPP_DISCO_INFO_NS, XMPP_IBR_NS, \
    XMPP_DISCO_ITEMS_NS, XMPP_PUBSUB_NS, XMPP_PUBSUB_EVENT_NS,\
    XMPP_PUBSUB_OWNER_NS

_all__ = ['Client']
  
class Client(component):
    Inboxes = {"inbox"      : "",
               "jid"        : "",
               "bound"      : "",
               "streamfeat" : "",
               "unhandled"  : "",
               "error"      : "",
               "control"    : "Shutdown the client stream"}
    
    Outboxes = {"outbox"  : "",
                "forward" : "",
                "log"     : "",
                "doauth"  : "",
                "signal"  : "Shutdown signal",
                "askregistration" : "",
                "askunregistration" : ""}

    def __init__(self, username, password, domain, resource=u"headstock", 
                 hostname=u'localhost', port=5222, usetls=False, register=False,
                 unregister=False, password_lookup =None,
                 log_file_path=None, log_to_console=False):
        super(Client, self).__init__() 
        self.jid = JID(username, domain, resource)
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port
        self.client = None
        self.graph = None
        self.domain = domain
        self.usetls = usetls
        self.register = register
        self.unregister = unregister
        self.password_lookup = self._get_pwd
        if password_lookup:
            self.password_lookup = password_lookup
        self.graph = None

        ClientStream.Outboxes["%s.query" % XMPP_IBR_NS] = "Registration"
        ClientStream.Outboxes["%s.query" % XMPP_LAST_NS] = "Activity"
        ClientStream.Outboxes["%s.query" % XMPP_DISCO_INFO_NS] = "Discovery"
        ClientStream.Outboxes["%s.query" % XMPP_DISCO_ITEMS_NS] = "PubSub Discovery of Nodes"
        ClientStream.Outboxes["%s.subscribe" % XMPP_PUBSUB_NS] = "Pubsub subscription handler"
        ClientStream.Outboxes["%s.unsubscribe" % XMPP_PUBSUB_NS] = "Pubsub unsubscription handler"
        ClientStream.Outboxes["%s.subscriptions" % XMPP_PUBSUB_NS] = "Pubsub subscriptions handler"
        ClientStream.Outboxes["%s.affiliations" % XMPP_PUBSUB_NS] = "Pubsub affiliations handler"
        ClientStream.Outboxes["%s.create" % XMPP_PUBSUB_NS] = "Pubsub node creation handler"
        ClientStream.Outboxes["%s.configure" % XMPP_PUBSUB_OWNER_NS] = "Pubsub node configuration handler"
        ClientStream.Outboxes["%s.purge" % XMPP_PUBSUB_NS] = "Pubsub node purge handler"
        ClientStream.Outboxes["%s.delete" % XMPP_PUBSUB_OWNER_NS] = "Pubsub node delete handler"
        ClientStream.Outboxes["%s.publish" % XMPP_PUBSUB_NS] = "Pubsub item publication handler"
        ClientStream.Outboxes["%s.retract" % XMPP_PUBSUB_NS] = "Pubsub item deletion handler"
        ClientStream.Outboxes["%s.items" % XMPP_PUBSUB_NS] = "Pubsub item retrieval handler"
        ClientStream.Outboxes["%s.x" % XMPP_PUBSUB_EVENT_NS] = ""
        ClientStream.Outboxes["%s.event" % XMPP_PUBSUB_EVENT_NS] = ""

        self.stream = ClientStream(self.jid, self.password_lookup, use_tls=self.usetls)

        self.base_graph = dict(client = self,
                               logger = Logger(path=log_file_path, stdout=log_to_console),
                               tcp = TCPClient(self.hostname, self.port),
                               xmlparser = XMLIncrParser(),
                               xmpp = self.stream,
                               streamerr = StreamError(),
                               saslerr = SaslError(),
                               jidsplit = Fanout(['client', 'contactjid', 'presencejid', 'chatjid',
                                                  'pubsubnodejid', 'discojid', 'registerjid', 'cotjid']),
                               boundsplit = Fanout(['client', 'chatbound', 'contactbound',
                                                    'pubsubnodebound', 'discobound', 'cotbound']),

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
                                           ("xmpp", "jid"): ("jidsplit", "inbox"),
                                           ("xmpp", "bound"): ("boundsplit", "inbox"),
                                           ("xmpp", "features"): ("client", "streamfeat"),
                                           ("xmpp", "unhandled"): ("client", "unhandled"),
                                           ("xmpp", "error"): ("client", "error"),
                                           ("jidsplit", "client"): ("client", "jid"),
                                           ("boundsplit", "client"): ("client", "bound"),
                                           ("client", "doauth"): ("xmpp", "auth")})

    def _get_pwd(self, jid):
        return self.password

    def registerComponents(self, components, linkages):
        if self.graph:
            self.graph.components.update(components)
            self.graph.addExternalPostboxes()

            for componentRef,sourceBox in linkages:
                toRef, toBox = linkages[(componentRef,sourceBox)]
                fromComponent = self.graph.components.get(componentRef, self.graph)
                toComponent = self.graph.components.get(toRef, self.graph)
                    
                passthrough = 0
                if fromComponent == self.graph: passthrough = 1
                if toComponent == self.graph: passthrough = 2
                if (fromComponent == self.graph) and (toComponent == self.graph):
                    passthrough = 0
                    print "WARNING, assuming linking outbox to inbox on the graph. This is a poor assumption"
                        
                self.graph.link((fromComponent,sourceBox), (toComponent,toBox), passthrough=passthrough)
                self.graph.addChildren(*self.graph.components.values())
                    
            for component in components.values():
                component.activate()
        else:
            self.base_graph.update(components)
            self.base_graph['linkages'].update(linkages)

    def get_component(self, key):
        return self.base_graph.get(key, None)

    def close(self):
        if self.unregister:
            self.send(None, 'askunregistration')
        else:            
            stanza = Presence.to_element(Presence(self.jid, type=u'unavailable')).xml(omit_declaration=True)
            self.send(stanza, 'outbox')
            self.send('OUTGOING : %s' % stanza, 'log')
            self.send('OUTGOING : </stream:stream>', 'log')
            self.send('</stream:stream>', 'outbox') 

    def shutdown(self):
        o = OneShot(msg=shutdownMicroprocess())
        o.link((o, 'outbox'), (self, 'control'))
        o.activate()

    def active(self):
        pass

    def unhandled_stanza(self, stanza):
        self.send(('UNHANDLED', msg), 'log')

    def initializeComponents(self):
        self.graph = Graphline(**self.base_graph)
        self.addChildren(self.graph)
        self.graph.activate()

        return 1

    def main(self):
        yield self.initializeComponents()

        self.running = True
        while self.running:
            if self.dataReady("control"):
                mes = self.recv("control")

                if isinstance(mes, shutdownMicroprocess) or \
                       isinstance(mes, producerFinished):
                    self.close()
                    self.running = False
                    yield 1

            if self.dataReady("unhandled"):
                stanza = self.recv('unhandled')
                self.unhandled_stanza(stanza)
                
            if self.dataReady("inbox"):
                self.recv('inbox')

            if self.dataReady("streamfeat"):
                feat = self.recv('streamfeat')
                if self.register and not feat.register:
                    self.send("The server does not support in-band registration. Closing connection.", 'log')
                    self.abort()
                else:
                    self.send(feat, 'doauth')
                
            if self.dataReady("jid"):
                self.jid = self.recv('jid')
                
            if self.dataReady("bound"):
                self.recv('bound')
                self.active()

            if self.dataReady("error"):
                e = self.recv('error')
                self.send(('INCOMING', e), "log")
                err = Error.from_element(e)
                if err.condition in ['not-authorized', 'failure'] and self.register:
                    self.send((self.username, self.password), 'askregistration')
                
            if self.running and not self.anyReady():
                self.pause()
  
            yield 1

        if self.unregister:
            self.send(None, 'askunregistration')
                    
        for child in self.graph.children:
            linkage = self.graph.link((self.graph, "signal"), (child, "control"))
            self.graph.send(shutdownMicroprocess(), 'signal')
            self.graph.unlink(thelinkage=linkage)

        yield shutdownMicroprocess(self, self.children)
        

if __name__ == '__main__':
    
    def parse_commandline():
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-d", "--xmpp-domain", dest="domain",
                          help="XMPP server domain (default: localhost)")
        parser.set_defaults(domain='localhost')
        parser.add_option("-a", "--address", dest="address", action="store",
                           help="XMPP server address (default: localhost:5222) ")
        parser.set_defaults(address='localhost:5222')
        parser.add_option("-u", "--username", dest="username",
                          help="XMPP username", action="store")
        parser.set_defaults(username=None)
        parser.add_option("-p", "--password", action="store", dest="password",
                          help="XMPP password. You may also be prompted for it if you do not pass this parameter")
        parser.set_defaults(password=None)
        parser.add_option("-r", "--register", action="store_true", dest="register",
                          help="Register the user if the server supports in-band registration (default: False)")
        parser.set_defaults(register=False)
        parser.add_option("-t", "--usetls", dest="usetls", action="store_true",
                           help="Use TLS (default: False)")
        parser.set_defaults(usetls=False)
        (options, args) = parser.parse_args()

        return options

    def add_extensions(client):
        from headstock.client.registration import make_linkages
        components, linkages = make_linkages()
        client.registerComponents(components, linkages)
        
        from headstock.client.presence import make_linkages
        components, linkages = make_linkages()
        client.registerComponents(components, linkages)

        from headstock.client.roster import make_linkages
        components, linkages = make_linkages()
        client.registerComponents(components, linkages)

        from headstock.client.im import make_linkages
        components, linkages = make_linkages()
        client.registerComponents(components, linkages)
         
        from headstock.client.pubsub import make_linkages
        components, linkages = make_linkages(u'pubsub.localhost')
        client.registerComponents(components, linkages)

        #from headstock.client.cot import make_linkages
        #components, linkages = make_linkages(load_cot_scripts())
        #client.registerComponents(components, linkages)

    def load_cot_scripts():
        from headstock.lib.cot import CotScript
        cots = []
        
        from bridge.common import XMPP_ROSTER_NS
        cots.append(('query', XMPP_ROSTER_NS, CotScript().load('RosterTest.cot')))

        return cots

    def run():
        from Axon.Scheduler import scheduler 
        scheduler.immortalise()
        options = parse_commandline()
        if not options.password:
            from getpass import getpass
            options.password = getpass()
        host, port = options.address.split(':')
        client = Client(unicode(options.username), 
                        unicode(options.password), 
                        unicode(options.domain),
                        hostname=host, port=int(port),
                        usetls=options.usetls,
                        register=options.register,
                        log_to_console=True)
        add_extensions(client)
        client.run()

    run()
