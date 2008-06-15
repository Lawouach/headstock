# -*- coding: utf-8 -*-
import sys
import os
import socket
from optparse import OptionParser

from Axon.Scheduler import scheduler 

from cherrypy.process import bus
from cherrypy.process import plugins, servers

from microblog.jabber.client import Client
from microblog.jabber.atomhandler import FeedReaderComponent
from microblog.jabber.monitor import HTTPResourceMonitor
from microblog.jabber.profile import ProfileHandler, NewProfileHandler
from microblog.atompub.application import AtomPubApplication
from microblog.profile.manager import ProfileManager

base_dir = os.getcwd()

def parse_commandline():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--xmpp-domain", dest="domain",
                      help="XMPP server domain (default: localhost)")
    parser.set_defaults(domain='localhost')
    parser.add_option("-a", "--address", dest="address", action="store",
                       help="XMPP server address (default: localhost:5222) ")
    parser.set_defaults(address='localhost:5222')
    (options, args) = parser.parse_args()

    return options

class Server(object):
    def __init__(self):
        self.running = True
        self.options = parse_commandline()

        host, port = self.options.address.split(':')
        Client.Host = unicode(host)
        Client.Port = int(port)
        Client.Domain = unicode(self.options.domain)

        self.atompub = AtomPubApplication(base_dir)

    def start(self):
        httpMonitor = HTTPResourceMonitor(30.0)
        httpMonitor.activate()

        newProfileFeedReader = FeedReaderComponent()
        newProfileFeedReader.activate()

        newProfileHandler = NewProfileHandler(base_dir, self.atompub)
        newProfileHandler.link((newProfileFeedReader, 'outbox'), (newProfileHandler, 'inbox'))
        newProfileHandler.activate()

        from Kamaelia.Util.OneShot import OneShot
        shot = OneShot()
        httpMonitor.link((shot, 'outbox'), (httpMonitor, 'monitor'))
        shot.send(('http://localhost:8080/profile/new/feed', newProfileFeedReader))

        profileFeedReader = FeedReaderComponent()
        profileFeedReader.activate()

        profileHandler = ProfileHandler(base_dir, self.atompub)
        profileFeedReader.link((profileFeedReader, 'outbox'), (profileHandler, 'inbox'))
        profileHandler.activate()

        from Kamaelia.Util.OneShot import OneShot
        shot = OneShot()
        httpMonitor.link((shot, 'outbox'), (httpMonitor, 'monitor'))
        shot.send(('http://localhost:8080/profile/feed', profileFeedReader))

        self.running = True

    start.priority = 90

    def stop(self):
        for client in Client.Sessions:
            Client.Sessions[client].shutdown()
        Client.Sessions.clear()
        self.running = False

    def exit(self):
        self.stop()

    def run_components(self):
        while self.running:
            try:
                for i in scheduler.run.main(0.02, canblock=True):
                    if not self.running:
                        break
            except KeyError, ke:
                print ke
                pass

def setup(server):
    import cherrypy
    cherrypy.server.unsubscribe()
    plugins.SignalHandler(bus)
    bus.subscribe('start', server.start)
    bus.subscribe('graceful', server.stop)
    bus.subscribe('exit', server.exit)

def serve(s):
    bus.start_with_callback(s.run_components)
    bus.block()

if __name__ == '__main__':
    s = Server()
    setup(s)
    serve(s)
