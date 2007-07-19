# -*- coding: utf-8 -*-

from datetime import datetime

from headstock.application.storage import Storage
from headstock.protocol.core.stanza import StanzaError
from headstock.application.server import SessionStreamProvider, make_threaded_server
from bridge import Element as E
from bridge import ENCODING
from headstock.protocol.extension.inbandregistration import InBandRegistration
from bridge.common import XMPP_IBR_NS
from headstock.protocol.core.iq import Iq
from headstock.lib.utils import generate_unique
from headstock.application.entity import Entity, Tracker
from headstock.error import HeadstockInvalidStanzaError
from headstock.protocol.core.jid import JID
from headstock.api.error import Error
from headstock.protocol.core.stream import DISCONNECTED, BOUND, AVAILABLE
from headstock.application.entity import Contact, Group, Resource, Entity
        
def cert_passphrase():
    return "test"

class Provider(SessionStreamProvider):
    def __init__(self, handler):
        SessionStreamProvider.__init__(self, handler)

        self.stream.proxy_registry.set_logger(handler.server.logger)

        #self.storage = Storage('sqlite', config={'Database': ':memory:'})
        self.storage = handler.server.storage

    def get_entity(self):
        return Entity.lookup_by_username(self.stream.username)

    def disconnected(self):
        SessionStreamProvider.disconnected(self)
        e = Entity.lookup_by_username(self.stream.username)
        if e != None:
            e.status = DISCONNECTED
            self.storage.save(e)
        
    def bound(self):
        SessionStreamProvider.bound(self)
        e = Entity.lookup_by_username(self.stream.username)
        if e != None:
            e.nodeid = self.stream.jid.nodeid()
            e.status = BOUND
            has_it = False
            for rs in e.Resource():
                if rs.value == self.stream.jid.resource:
                    has_it = True
                    break
            if not has_it:
                r = Resource()
                r.value = self.stream.jid.resource
                r.entity_id = e.ID
                self.storage.save(r)
            self.storage.save(e)
    
    def track_login(self, user):
        tr = user.Tracker()
        if tr == None:
            tr = Tracker()
            user.add(tr)
        tr.last_ip = self.handler.client_address[0]
        tr.last_login_timestamp = datetime.now()
        self.storage.save(tr)

    def track_logout(self, user):
        tr = user.Tracker()
        if tr == None:
            tr = Tracker()
            user.add(tr)
        tr.last_logout_timestamp = datetime.now()
        self.storage.save(tr)
    
    def get_password(self, username):
        e = Entity.lookup_by_username(username)
        if e != None:
            return e.password
 
    def registration_fields(self):
        children = [E(u'instructions', content=u'Choose a username and password to register with this server',
                      namespace=XMPP_IBR_NS),
                    E(u'username', namespace=XMPP_IBR_NS),
                    E(u'password', namespace=XMPP_IBR_NS)]
        iq = InBandRegistration.create_ibr_result(elements=children, stanza_id=generate_unique())
        self.stream.propagate(element=iq)

    def registration_submitted(self, ri):
        e = Entity.lookup_by_username(ri.fields['username'])
        if e != None:
            iq = Iq.create_error_iq(from_jid=self.stream.node_name, stanza_id=ri.stanza_id)
            query = E(u'query', namespace=XMPP_IBR_NS, parent=iq)
            E(u'username', content=ri.fields['username'], namespace=XMPP_IBR_NS, parent=query)
            E(u'password', content=ri.fields['password'], namespace=XMPP_IBR_NS, parent=query)
            iq.xml_children.append(StanzaError.create_conflict())
            self.stream.propagate(element=iq)
            return

        e = Entity()
        e.username = ri.fields['username']
        e.password = ri.fields['password']
        self.storage.save(e)
        
        iq = Iq.create_result_iq(stanza_id=generate_unique())
        self.stream.propagate(element=iq)

    def contacts_requested(self, stanza, contact):
        from headstock.api.contact import Contact
        e = Entity.lookup_by_nodeid(self.stream.jid.nodeid())

        cts = e.Contact()
        for ct in cts:
            c = Contact(self.sess, ct.jid)
            c.subscription = ct.from_state
            c.name = ct.name
            c.state = ct.state
            c.availability = ct.status
            for gr in ct.Group():
                c.groups.append(gr.value)
            contact.contacts.append(c)
            
        contact.send_contacts(stanza_id=stanza.id)
        
    def subscription_requested(self, stanza, contact):
        e = Entity.lookup_by_nodeid(self.stream.jid.nodeid())

        ct = Contact.lookup_by_entity_and_fulljid(e, contact.jid)
        if not ct:
            ct = Contact()

        ct.jid = unicode(contact.jid)
        ct.from_state = u'none'
        ct.to_state = u'out'
        ct.state = contact.state
        ct.entity_id = e.ID
        ct.name = contact.name
        ct.status = contact.availability
        e.add(ct)
        self.storage.save(ct)
                
        contact.push(stanza_id=stanza.id)
        
    def subscription_allowed(self, stanza):
        pass

    def online(self, stanza, contact):
        e = Entity.lookup_by_nodeid(self.stream.jid.nodeid())
        e.status = AVAILABLE
        self.storage.save(e)

        contact.set_jid(self.stream.jid)

        # First we return the contact list to the client
        from headstock.api.contact import Contact
        cts = e.Contact()
        for ct in cts:
            c = Contact(self.sess, ct.jid)
            c.subscription = ct.from_state
            c.name = ct.name
            c.availability = ct.status
            c.state = ct.state
            for gr in ct.Group():
                c.groups.append(gr.value)
            contact.contacts.append(c)

        contact.send_contacts(to_jid=unicode(self.stream.jid),
                              stanza_id=stanza.id)

        # Then we probe contacts for availability
        #contact.probe_contacts()

        # Then we propagate the presence to the client's contacts
        # which have a subscription in 'from', 'both'
        contact.inform_of_presence()        
            
    def contacts_submitted(self, stanza, contact):
        e = Entity.lookup_by_nodeid(self.stream.jid.nodeid())
        
        for c in contact.contacts:
            # First we attach the submitted contact to the
            # sender account
            ct = Contact.lookup_by_entity_and_fulljid(e, c.jid)
            if not ct:
                ct = Contact()

            ct.jid = unicode(c.jid)
            ct.from_state = u'none'
            ct.to_state = u'out'
            ct.entity_id = e.ID
            ct.name = c.name
            ct.status = c.availability
            e.add(ct)
            self.storage.save(ct)
                
            for group in c.groups:
                gr = Group()
                gr.value = group
                ct.add(gr)
                self.storage.save(gr)

            # Then we attach the sender account to
            # each submitted contact
            ct = Contact.lookup_by_entity_and_fulljid(e, c.jid)
        
        contact.push_contacts(stanza_id=stanza.id)
        
def init_storage(log):
    storage = Storage('psycopg', config={'Connect': 'host=localhost dbname=xmpptest user=sylvain password=test'})
    storage.log_sql(log)
    #storage.reset()
    return storage
        
def setup():
    server = make_threaded_server('localhost', 5232, u'localhost', Provider)
    server.set_logger('./server.log', True)
    server.set_ssl_details(file('./server.crt', 'r').read(),
                           file('./server.key', 'r').read(),
                           cert_passphrase)
    server.set_storage(init_storage(server.log))
    
    return server
    
if __name__ == '__main__':
    server = setup()
    server.run()
