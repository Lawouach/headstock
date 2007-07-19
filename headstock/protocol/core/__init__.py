#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['Entity']

class Entity(object):
    def __init__(self, stream, proxy_registry=None):
        self.stream = stream
        self.proxy_registry = proxy_registry

        # headstock.protocol.core.stanza.Stanza instance
        self.stanza = None

    def initialize_dispatchers(self):
        raise NotImplemented

    def cleanup_dispatchers(self):
        raise NotImplemented
    
