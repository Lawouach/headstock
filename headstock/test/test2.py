# -*- coding: utf-8 -*-

from headstock.application.client import ThreadedBaseClient
from headstock.protocol.core.message import Message
from headstock.api.im import Body, Event
from headstock.api.contact import Contact
from headstock.api.discovery import Discovery, Feature, Identity
from headstock.api.version import VersionInfo

from bridge import Element as E
from bridge.common import XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS, \
     XMPP_OOB_NS, XMPP_SI_NS, XMPP_SI_FILE_TRANSFER_NS, XMPP_BYTESTREAMS_NS
from bridge.parser import DispatchParser

from headstock.application.storage import Storage

import time, sys, Queue


def cert_passphrase():
    return "test"

class Demo(ThreadedBaseClient):
    def __init__(self):
        ThreadedBaseClient.__init__(self, 'localhost', 5232)

        #self.storage = Storage('sqlite', config={'Database': ':memory:'})
        
    def version_info_received(self, info):
        print info
        
    def say_hello(self):
        pass
        #print self.sess.contacts.contacts
##         if 'test2@localhost' in self.sess.contacts.contacts:
##             self.sess.contacts.contacts['test2@localhost'].groups.append(u'another one bytes the dust')
##             self.sess.contacts.contacts['test2@localhost'].propagate_modifications()

        ## for jid in self.session.contacts.contacts:
##             contact = self.session.contacts.contacts[jid]
##             if contact.availability:
##                 #contact.im.chat(u'hello', lang=u'en-GB')
##                 #contact.ichat(u'\xe9', lang=u'fr-FR')
##                 #contact.isuggest_resource_at(Body(u'check this'),
##                 #                               u'http://www.defuze.org/oss/misc/sylvain.jpg',
##                 #                               desc=u'nice pix')
                
##                 #contact.ask_last_seen()
##                 #contact.resource_at(u'http://www.defuze.org/oss/misc/sylvain.jpg')

    def disco_retrieved(self, disco):
        for feat in disco.features:
            print feat

        if disco.data_form:
            #self.sess.pubsub.ask_subscriptions(u'pubsub.localhost')
            #self.sess.pubsub.ask_affiliations(u'pubsub.localhost')
            print disco.data_form
            for field in disco.data_form.fields:
                print field

    def pubsub_subscriptions(self, subs):
        for sub in subs:
            print sub
            #self.sess.discovery.ask_items(u'pubsub.localhost', node_name=sub.node)

    def subscription_requested(self, contact):
        contact.accept_subscription()

    def bound(self):
        ThreadedBaseClient.bound(self)
        #self.session.version.ask(u'test@localhost')
        #self.session.registration.cancel_registration(u'test6@localhost')
        #self.session.registration.change_password(u'localhost', u'test', u'test')

        #self.session.privacy_list.ask_available_privacy_lists()
        #self.session.privacy_list.reset_privacy_list(u'public')
        #self.session.privacy_list.ask_privacy_list(u'public')

        #self.session.ask_offline_messages()

        #self.session.rpc.call(u'test6@localhost', 'echo', ('hello there',))
        #c = Contact(self.sess, u'test2@localhost')
        #c.subscribe()
        
    def register(self, sasl, e):
        print "Ask for registration details..."
        self.session.registration.ask_registration_fields()

    def registration_fields(self, ri, instructions):
        print "Instructions: ", instructions, ri
        from headstock.api.registration import RegistrationInfoDataForm
        from headstock.api.registration import RegistrationInfo
        if isinstance(ri, RegistrationInfo):
            ri = RegistrationInfo()
            ri.fields[u'username'] = u'test'
            ri.fields[u'password'] = u'test'
            self.session.registration.send_registration_details(ri)
        elif isinstance(ri, RegistrationInfoDataForm):
            field = ri.form.field_by_var('username')
            field.values.append(u'test')
            field = ri.form.field_by_var('password')
            field.values.append(u'test')
            self.session.registration.send_registration_details(ri)

    def registered(self):
        print "Registered!"

    def unregistered(self):
        print "Unregistered!"

    def registration_conflict(self, ri):
        print "Conflict"

    def privacy_list_not_found(self, name):
        print "Server does not have a privacy list named: ", name
        
    def setup(self):
        self.set_jid_details(u'localhost', u'test', u'test') #, u'headstock')
        self.set_version(VersionInfo(u'headstock', u'0.1.0', u'Linux'))
        #self.set_ssl_details(file('./server.crt', 'r').read(),
        #                     file('./server.key', 'r').read(),
        #                     cert_passphrase)
        self.set_logger('./test.log', True)
  #      self.storage.log_sql(self.log)
 #       self.storage.reset()
        
        ThreadedBaseClient.setup(self)
        
        self.session.contacts.on_update(self.say_hello)
##         #self.session.discovery.on_retrieved(self.disco_retrieved)
##         self.session.discovery.on_infos_requested(self.info_requested)
##         #self.session.pubsub.on_subscriptions_update(self.pubsub_subscriptions)
##         #self.session.version.on_received(self.version_info_received)
##         #self.session.registration.ask_registration_fields()
        self.stream.sasl_error.register_not_authorized(self.register)

        self.session.registration.on_registration_fields_received(self.registration_fields)
        self.session.registration.on_registered_successfully(self.registered)
        self.session.registration.on_unregistered_successfully(self.unregistered)
        self.session.registration.on_conflict_detected(self.registration_conflict)
        self.session.privacy_list.on_list_not_found(self.privacy_list_not_found)

##         self.session.contacts.on_subscription_requested(self.subscription_requested)
        
if __name__ == '__main__':
    demo = Demo()
    try:
        demo.setup()
        demo.start()
    except KeyboardInterrupt:
        demo.stop()
    except Exception, ex:
        print ex
        demo.stop()
        raise
    
