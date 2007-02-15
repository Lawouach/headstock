import sys
import os
import imp
import threading

from bridge.parser.bridge_expat import Parser
from bridge import Element as E
E.parser = Parser
from bridge.parser.incremental import create_parser

from headstock.core.stream import Stream
from headstock.handler.client import *


class PresenceHandler(object):
    def user_online(self, p, e):
        print unicode(e.get_attribute('from'))
    
    def user_unavailable(self, p, e):
        print unicode(e.get_attribute('from'))

    def user_subscription_requested(self, p, e):
        jid = unicode(e.get_attribute('from'))
        p.allow_subscription(jid)

class StreamErrorHandler(object):
    def any_error(self, stream_error, e):
        print "################## STREAM ERROR #################"
        print e.xml()
        print "################## STREAM ERROR #################"
        stream_error.stream.terminate()
        stream_error.stream.client.disconnect()

class SaslErrorHandler(object):
    def authentication_failed(self, sasl_error, e):
        print "################## SASL ERROR #################"
        print e.xml()
        print "################## SASL ERROR #################"

class StreamHandler(object):
    def __init__(self, target):
        self.target = target
        
    def connected(self, stream):
        pass

    def authenticated(self, stream):
        pass

    def bound(self, stream):
        self.target(stream)

def launch_stream(username, password, target):
    cert = file('./server.crt', 'r').read()
    pkey = file('./server.key', 'r').read()

    def cert_passphrase():
        return "test"
    
    c = AsyncClient('localhost', 5222, cert, pkey, cert_passphrase)
    parser, handler, output = create_parser()
    c.set_parser(parser)
    c.set_handler(handler)
    c.connect()

    target = load_target(target)
    stream_handler = StreamHandler(target)
    stream_error_handler = StreamErrorHandler()
    sasl_error = SaslErrorHandler()

    s = Stream(u'localhost', c)
    #s.use_tls = True
    s.set_auth(username, password)
    s.set_resource_name(u'headstock')
    s.cond = threading.Condition()
    s.register_on_bound(stream_handler.bound)
    s.stream_error.register_default_dispatcher(stream_error_handler.any_error)
    s.stanza_error.register_default_dispatcher(stream_error_handler.any_error)
    s.sasl_error.register_not_authorized(sasl_error.authentication_failed)
    s.initialize_all()

    presence_handler = PresenceHandler()
    p = s.presence
    p.register_online(presence_handler.user_online)
    p.register_unavailable(presence_handler.user_unavailable)
    p.register_subscribe(presence_handler.user_subscription_requested)

    return c, s

def load_target(name):
    file, pathname, description = imp.find_module(name, [os.getcwd()])
    mod = imp.load_module(name, file, pathname, description)
    return mod.run

def run():
    c, s = launch_stream(sys.argv[1], sys.argv[2], sys.argv[3])
    s.initiate()

    import asyncore
    asyncore.loop()

if __name__ == '__main__':
    run()
