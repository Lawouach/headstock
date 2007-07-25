#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Entity', 'Foreign']

class Entity(object):
    def __init__(self, from_jid=None, to_jid=None):
        self.from_jid = from_jid
        self.to_jid = to_jid

    def swap_jids(self):
        self.from_jid, self.to_jid = self.to_jid, self.from_jid

class Foreign(object):
    def __init__(self, e):
        self.e = e

    def __repr__(self):
        return '<Foreign at %s>' % (hex(id(self)),)
