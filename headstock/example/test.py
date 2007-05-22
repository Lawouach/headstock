# -*- coding: utf-8 -*-

from headstock.lib.network.threadedclient import ThreadedClient
from headstock.protocol.core.stream import Stream
from headstock.protocol.core.message import Message
from headstock.api.session import Session
from headstock.api.im import Body, Event
from headstock.api.discovery import Discovery, Feature, Identity
from headstock.api.version import VersionInfo

from bridge import Element as E
from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS, \
     XMPP_OOB_NS, XMPP_SI_NS, XMPP_SI_FILE_TRANSFER_NS, XMPP_BYTESTREAMS_NS
from bridge.parser import DispatchParser

import time, sys, Queue

def cert_passphrase():
    return "test"

class Demo:
    def __init__(self):
        self.keep_alive = True
        self.c = ThreadedClient('localhost', 5222)
        parser = DispatchParser()
        self.c.set_parser(parser)

        self.s = Stream(self.c)
        self.s.initialize_all()
        
        self.sess = Session(self.s)
        self.sess.initialize_dispatchers()
        
    def loop(self):
        client = self.c
        parser = client.get_parser()
        while self.keep_alive:
            try:
                data = client.incoming.get(timeout=0.01)
                parser.feed(data)
            except Queue.Empty:
                pass

    def stop(self):
        if self.c.connected:
            self.s.terminate()
            self.c.disconnect()
            self.c.join()
            self.keep_alive = False
            self.s = self.c = None

    def version_info_received(self, info):
        print info
        
    def say_hello(self):
        event = Event(displayed=True)
   
        for jid in self.sess.contacts.contacts:
            contact = self.sess.contacts.contacts[jid]
            if contact.availability:
                #contact.ichat(u'hello', lang=u'en-GB')
                #contact.ichat(u'\xe9', lang=u'fr-FR')
                #contact.isuggest_resource_at(Body(u'check this'),
                #                               u'http://www.defuze.org/oss/misc/sylvain.jpg',
                #                               desc=u'nice pix')
                
                contact.ask_last_seen()
                #contact.resource_at(u'http://www.defuze.org/oss/misc/sylvain.jpg')

    def info_requested(self, from_jid):
        d = Discovery()
        d.identities.append(Identity(category=u'client', type=u'pc'))
        d.features.append(Feature(var=XMPP_DISCO_INFO_NS))
        d.features.append(Feature(var=XMPP_DISCO_ITEMS_NS))
        d.features.append(Feature(var=XMPP_OOB_NS))
        d.features.append(Feature(var=XMPP_SI_NS))
        d.features.append(Feature(var=XMPP_SI_FILE_TRANSFER_NS))
        d.features.append(Feature(var=XMPP_BYTESTREAMS_NS))
        self.sess.discovery.send_information(d, to_jid=from_jid)

    def disco_retrieved(self, disco):
        for feat in disco.features:
            print feat

        if disco.data_form:
            self.sess.pubsub.ask_subscriptions(u'pubsub.localhost')
            self.sess.pubsub.ask_affiliations(u'pubsub.localhost')
            print disco.data_form
            for field in disco.data_form.fields:
                print field

    def pubsub_subscriptions(self, subs):
        for sub in subs:
            print sub
            self.sess.discovery.ask_items(u'pubsub.localhost', node_name=sub.node)

    def doit(self):
        self.sess.discovery.ask_information(u'test3@localhost/ubuntu')
        self.sess.discovery.ask_items(u'test3@localhost/ubuntu')
        self.sess.version.ask(u'test3@localhost/ubuntu')
        self.sess.discovery.ask_items(u'pubsub.localhost')
        self.sess.discovery.ask_items(u'pubsub.localhost', node_name=u'/muse')
        #self.sess.discovery.ask_information(u'pubsub.localhost')
        #self.sess.pubsub.check_configure_support(u'pubsub.localhost', node_name=u'mooh')
        #self.sess.pubsub.subscribe(u'pubsub.localhost', node_name=u'/yeah')
        #self.sess.pubsub.create_node_whitelist(u'pubsub.localhost', node_name=u'yeah')
        #self.sess.pubsub.delete_node(u'pubsub.localhost', node_name=u'/yeah')
        #self.sess.pubsub.purge_items(u'pubsub.localhost', node_name=u'/muse')
        #payload = E.load('<test />').xml_root
        #self.sess.pubsub.publish(u'pubsub.localhost', node_name=u'/muse', payload=payload)
        
    def got_error(self, err):
        print err

    def run(self):
        #self.c.certificate = file('./server.crt', 'r').read()
        #self.c.certificate_key = file('./server.key', 'r').read()
        #self.c.certificate_password_cb = cert_passphrase

        self.sess.error.on_received(self.got_error)
        self.sess.contacts.on_update(self.say_hello)
        self.sess.discovery.on_retrieved(self.disco_retrieved)
        self.sess.discovery.on_infos_requested(self.info_requested)
        self.sess.pubsub.on_subscriptions_update(self.pubsub_subscriptions)
        self.sess.version.set(VersionInfo(u'headstock', u'0.1.0', u'Linux'))
        self.sess.version.on_received(self.version_info_received)
        self.s.register_on_bound(self.doit)
        self.s.set_node_name(u'ubuntu')
        self.s.set_auth(u'test', u'test')
        self.s.set_resource_name(u'ubuntu')
        self.c.connect()
        self.c.start()
        self.s.initiate()
        self.loop()

if __name__ == '__main__':
    demo = Demo()
    try:
        demo.run()
    except KeyboardInterrupt:
        demo.stop()
    except Exception, ex:
        demo.stop()
        raise
    
