#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.protocol.extension.inbandregistration import InBandRegistration
from headstock.lib.utils import generate_unique
from headstock.api.dataform import Data, Field
from headstock.api.storage import Entity
from bridge.common import XMPP_IBR_NS, XMPP_DATA_FORM_NS
from bridge import Element as E

__all__ = ['RegistrationInfo', 'RegistrationInfoDataForm', 'Registration']

class RegistrationInfo(object):
    def __init__(self):
        self.stanza_id = None
        self.registered = False
        self.fields = {}
       
    def __repr__(self):
        return '<RegistrationInfo at %s>' % (hex(id(self)))

class RegistrationInfoDataForm(object):
    def __init__(self):
        self.stanza_id = None
        self.registered = False
        self.form = Data(form_type=u'form')
        self.form.fields.append(Field(field_type=u'hidden',
                                      var=u'FORM_TYPE', values=[XMPP_IBR_NS]))
       
    def __repr__(self):
        return '<RegistrationInfoDataForm at %s>' % (hex(id(self)))

class Registration(object):
    def __init__(self, session):
        self.session = session

    @classmethod
    def from_element(cls, e):
        instructions = e.get_child('instructions', XMPP_IBR_NS)
        if instructions:
            instructions = instructions.xml_text

        stanza_id = e.xml_parent.get_attribute('id')
        use_data_form = e.get_child('x', XMPP_DATA_FORM_NS)
        if use_data_form:
            ri = RegistrationInfoDataForm()
            ri.stanza_id = unicode(stanza_id)
            ri.form = Data.from_element(use_data_form)
            if e.has_child('registered', XMPP_IBR_NS):
                ri.registered = True
        else:
            ri = RegistrationInfo()
            ri.stanza_id = unicode(stanza_id)
            for child in e.xml_children:
                if child.xml_ns == XMPP_IBR_NS:
                    ri.fields[child.xml_name] = child.xml_text

            if 'instructions' in ri.fields:
                del ri.fields['instructions']

            if 'registered' in ri.fields:
                ri.registered = True
                del ri.fields['registered']

        return ri, instructions

    def ask_registration_fields(self):
        iq = InBandRegistration.create_ibr_query(stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

    def registration_fields_requested(self, ibr, e):
        children = [E(u'instructions', namespace=XMPP_IBR_NS,
                      content=u'Choose a username and password to register with this server'),
                    E(u'username', namespace=XMPP_IBR_NS),
                    E(u'password', namespace=XMPP_IBR_NS),
                    E(u'email', namespace=XMPP_IBR_NS)]
        iq = InBandRegistration.create_ibr_result(elements=children, stanza_id=generate_unique())
        self.stream.propagate(element=iq)
            
    def registration_submitted(self, ibr, e):
        ri, instructions = self._from_element(e)
        e = Entity.lookup_by_username(ri.fields.get('username', None))
        if e != None:
            query = E(u'query', namespace=XMPP_IBR_NS)
            E(u'username', content=ri.fields.get('username', u''), namespace=XMPP_IBR_NS, parent=query)
            E(u'password', content=ri.fields.get('password', u''), namespace=XMPP_IBR_NS, parent=query)
            E(u'email', content=ri.fields.get('email', u''), namespace=XMPP_IBR_NS, parent=query)
            
            iq = StanzaError.create_conflict(from_jid=self.stream.node_name, stanza_id=ri.stanza_id,
                                             children = [query])
            self.stream.propagate(element=iq)
            return

        e = Entity()
        e.username = ri.fields.get('username', u'')
        e.password = ri.fields.get('password', u'')
        e.email = ri.fields.get('email', u'')
        self.storage.save(e)
        
        iq = Iq.create_result_iq(stanza_id=generate_unique())
        self.stream.propagate(element=iq)

    def registration_success(self, ibr, e):
        if callable(self.registered_successfully):
            self.registered_successfully()
            
    def unregistration_success(self, ibr, e):
        pass
            
    def registration_fields_received(self, ibr, e):
        ri, instructions = self._from_element(e)
         
    def send_registration_details(self, ri):
        iq = InBandRegistration.create_ibr_registration(stanza_id=generate_unique())
        query = iq.get_child('query', XMPP_IBR_NS)
        
        if isinstance(ri, RegistrationInfo):
            for field in ri.fields:
                E(field, content=ri.fields[field], namespace=XMPP_IBR_NS,
                  prefix=query.xml_prefix, parent=query)
            self.session.stream.propagate(element=iq)
        elif isinstance(ri, RegistrationInfoDataForm):
            Data.to_element(ri.form, parent=query)
            self.session.stream.propagate(element=iq)
        
    def cancel_registration(self, from_jid):
        iq = InBandRegistration.create_ibr_unregistration(from_jid=from_jid,
                                                          stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)
        
    def change_password(self, to_jid, username, password):
        iq = InBandRegistration.create_ibr_change_password(to_jid=to_jid,
                                                           stanza_id=generate_unique(),
                                                           username=username,
                                                           password=password)
        self.session.stream.propagate(element=iq)

    def conflict_detected(self, error, e):
        ri, instructions = Registration.from_element(e)
