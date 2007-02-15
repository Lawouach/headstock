#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Entity(object):
    def __init__(self, stream, proxy_registry=None):
        self.stream = stream
        self.proxy_registry = proxy_registry

    def initialize_dispatchers(self):
        raise NotImplemented

    def cleanup_dispatchers(self):
        raise NotImplemented
    
