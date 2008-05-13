# -*- coding: utf-8 -*-
import sys
import os
import socket
import threading
from optparse import OptionParser

from cherrypy.process import bus
from cherrypy.process import plugins, servers

from microblog.jabber.client import Client
from microblog.web import setup_atompub

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
    parser.add_option("-w", "--web-only", dest="webonly", action="store_true",
                       help="Web server only (default: False)")
    parser.set_defaults(webonly=False)
    (options, args) = parser.parse_args()

    return options

class Server(object):
    def __init__(self):
        self.options = parse_commandline()
        self.client = None

        atompub = setup_atompub(base_dir)
        if not self.options.webonly:
            if not self.options.password:
                from getpass import getpass
                self.options.password = getpass()
            host, port = self.options.address.split(':')
            self.client = Client(atompub, unicode(self.options.username), 
                                 unicode(self.options.password), 
                                 unicode(self.options.domain),
                                 server=host, port=int(port),
                                 usetls=self.options.usetls,
                                 register=self.options.register)

    def start(self):
        if self.client:
            self.client.activate()
    start.priority = 90

    def stop(self):
        if self.client:
            self.client.shutdown()

    def exit(self):
        self.stop()

def setup(server):
    plugins.SignalHandler(bus)
    bus.subscribe('start', server.start)
    bus.subscribe('graceful', server.stop)
    bus.subscribe('exit', server.exit)

def serve_http_only():
    import cherrypy
    cherrypy.quickstart()

def serve():
    bus.start()
    try:
        try:
            from Axon.Scheduler import scheduler 
            scheduler.run.runThreads(slowmo=0.01) 
        except (KeyboardInterrupt, IOError):
            pass
        except SystemExit:
            pass
    finally:
        bus.exit()

if __name__ == '__main__':
    s = Server()
    setup(s)
    if s.options.webonly:
        serve_http_only()
    else:
        serve()
