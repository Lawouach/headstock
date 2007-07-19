#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.lib.utils import extract_from_stanza

__all__ = ['ProxyRegistry']

class ProxyRegistry(object):
    def __init__(self, stream):
        self.stream = stream
        self._dispatchers = {}
        self.logger = None
        
    def set_logger(self, logger):
        self.logger = logger
        
    def register(self, name, proxy_dispatcher, namespace=None):
        client = self.stream.get_client()
        parser = client.get_parser()
        parser.register_on_element(name, namespace=namespace,
                                   dispatcher=proxy_dispatcher)

    def cleanup(self, name, namespace=None):
        client = self.stream.get_client()
        parser = client.get_parser()
        parser.unregister_on_element(name, namespace=namespace)

    def add_dispatcher(self, name, dispatcher):
        self._dispatchers[name] = dispatcher

    def has_dispatcher(self, name):
        return name in self._dispatchers

    def dispatch(self, name, caller, e):
        if name in self._dispatchers:
            if self.logger:
                self.logger.debug("REGISTRY: %s %r" % (name, repr(self._dispatchers[name])))
            caller.stanza = extract_from_stanza(e)
            self._dispatchers[name](caller, e)
