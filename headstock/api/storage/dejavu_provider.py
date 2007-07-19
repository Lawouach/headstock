#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Dejavu is an ORM developed by Robert Brewer
# It can be found at http://projects.amor.org/dejavu
# headstock requires 1.5RC1 available at:
# http://projects.amor.org/releases/dejavu/

from headstock.api.storage import BaseStorage

import dejavu
arena = dejavu.Arena()

__all__ = ['arena', 'Storage',
           'Entity', 'Contact', 'Group', 'Resource', 'Tracker']

class Storage(BaseStorage):
    def __init__(self, type, config):
        arena.add_store("main", "%s" % (type, ), config)
        arena.register_all(globals())
        self.logger = None

    def set_logger(self, logger=None):
        if logger:
            arena.log = logger
            self.logger = logger
        arena.logflags += dejavu.logflags.SQL

    def reset(self):
        from headstock.application.entity import Tracker, Entity, \
             Group, Contact, Resource
        for cls in (Entity, Resource, Tracker, Group, Contact):
            if arena.has_storage(cls):
                arena.drop_storage(cls)

        for cls in (Entity, Resource, Tracker, Group, Contact):
            arena.create_storage(cls)

    def save(self, unit, **kwargs):
        sandbox = unit.sandbox
        if not sandbox:
            sandbox = arena.new_sandbox()     
            sandbox.memorize(unit)
        sandbox.flush_all()
        if self.logger:
            self.logger("Committed %r" % unit, "STORAGE:")
        return unit

##############################################################
# Mapping to the storage entities
##############################################################
import datetime
from dejavu import Unit, UnitProperty

class Entity(Unit):
    nodeid = UnitProperty(unicode)
    username = UnitProperty(unicode)
    password = UnitProperty(unicode)
    email = UnitProperty(unicode)
    status = UnitProperty(int)

    @classmethod
    def lookup_by_username(self, username):
        sandbox = arena.new_sandbox()
        return sandbox.unit(Entity, username=username)

    @classmethod
    def lookup_by_nodeid(self, nodeid):
        sandbox = arena.new_sandbox()
        return sandbox.unit(Entity, nodeid=nodeid)
    
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
    
    @classmethod
    def lookup_by_entity_and_fulljid(self, entity, jid):
        sandbox = arena.new_sandbox()
        
        f = lambda c: c.jid == unicode(jid) and c.entity_id == entity.ID
        return sandbox.unit(Contact, f)

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
