#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from dejavu import Unit, UnitProperty
from headstock.application.storage import arena

__all__ = ['Entity', 'Contact', 'Group', 'Resource', 'Tracker']

class Entity(Unit):
    nodeid = UnitProperty(unicode)
    username = UnitProperty(unicode)
    password = UnitProperty(unicode)
    status = UnitProperty(int)
    

    def lookup_by_username(self, username):
        sandbox = arena.new_sandbox()
        return sandbox.unit(Entity, username=username)
    lookup_by_username = classmethod(lookup_by_username)

    def lookup_by_nodeid(self, nodeid):
        sandbox = arena.new_sandbox()
        return sandbox.unit(Entity, nodeid=nodeid)
    lookup_by_nodeid = classmethod(lookup_by_nodeid)
    
class Tracker(Unit):
    last_ip = UnitProperty(unicode)
    last_login_timestamp = UnitProperty(datetime.datetime)
    last_logout_timestamp = UnitProperty(datetime.datetime)
    status = UnitProperty(int)
    
class Contact(Unit):
    entity_id = UnitProperty(int, index=True)
    jid = UnitProperty(unicode)
    name = UnitProperty(unicode)
    status = UnitProperty(int)
    from_state = UnitProperty(unicode)
    to_state = UnitProperty(unicode)
    state = UnitProperty(unicode)
    
    def lookup_by_entity_and_fulljid(self, entity, jid):
        sandbox = arena.new_sandbox()
        
        f = lambda c: c.jid == unicode(jid) and c.entity_id == entity.ID
        return sandbox.unit(Contact, f)
    lookup_by_entity_and_fulljid = classmethod(lookup_by_entity_and_fulljid)

class Resource(Unit):
    entity_id = UnitProperty(int, index=True)
    value = UnitProperty(unicode)
    
class Group(Unit):
    value = UnitProperty(unicode)
    contact_id = UnitProperty(int, index=True)

Entity.one_to_one('ID', Tracker, 'ID')
Entity.one_to_many('ID', Contact, 'entity_id')
Entity.one_to_many('ID', Resource, 'entity_id')
Contact.one_to_many('ID', Group, 'contact_id')
