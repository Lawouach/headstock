#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dejavu
arena = dejavu.Arena()

__all__ = ['arena', 'Storage']

class Storage(object):
    def __init__(self, type, config):
        arena.add_store("main", "%s" % (type, ), config)
        arena.register_all(globals())
        self.logger = None

    def log_sql(self, logger=None):
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

    def save(self, unit):
        sandbox = unit.sandbox
        if not sandbox:
            sandbox = arena.new_sandbox()     
            sandbox.memorize(unit)
        sandbox.flush_all()
        if self.logger:
            self.logger("Committed %r" % unit, "STORAGE:")
        return unit
