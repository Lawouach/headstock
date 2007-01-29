#!/usr/bin/env python
# -*- coding: utf-8 -*-

from inspect import getmembers, ismethod

__all__ = ['Registry']

class Registry:
    def __init__(self, inst=None):
        pass

    def run(self, operation, *args, **kwargs):
        handler_name = 'handle_%s' % operation
        if hasattr(self, handler_name):
            cb = getattr(self, handler_name)
            cb(*args, **kwargs)

    def register(self, name, cb):
        """
        Registers a callable to be applied to a XMPP response
        starting with the element 'name'.

        Keyword arguments:
        name -- local name of the XML element
        cb -- Python callable
        """
        name = name.replace('-', '_')
        setattr(self, 'handle_%s' % name, cb)

    def register_connected(self, cb):
        self.handle_connected = cb

    def register_authenticated(self, cb):
        self.handle_authenticated = cb

    def register_bound_to_resource(self, cb):
        self.handle_bound = cb
