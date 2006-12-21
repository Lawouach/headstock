#!/usr/bin/env python
# -*- coding: utf-8 -*-

from inspect import getmembers, ismethod

__all__ = ['Registry']

class Registry(dict):
    def __init__(self, inst=None):
        dict.__init__(self)

    def run(self, operation, *args, **kwargs):
        if operation in self:
            self[operation](*args, **kwargs)

    @classmethod
    def register_class(cls, inst):
        members = getmembers(inst)
        registry = Registry()
        for (name, member) in members:
            if ismethod(member) and hasattr(member, 'headstock'):
                registry[member.headstock] = member

        return registry            
        
