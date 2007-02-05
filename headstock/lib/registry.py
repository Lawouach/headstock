#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['ProxyRegistry']

class ProxyRegistry(object):
    def __init__(self, stream):
        self.stream = stream
        self._dispatchers = {}
        
    def register(self, name, proxy_dispatcher, namespace=None):
        client = self.stream.get_client()
        handler = client.get_handler()
        handler.register_on_element(name, namespace=namespace,
                                    dispatcher=proxy_dispatcher)

    def cleanup(self, name, namespace=None):
        handler.unregister_on_element(name, namespace=namespace)

    def add_dispatcher(self, name, dispatcher):
        self._dispatchers[name] = dispatcher

    def dispatch(self, name, caller, e):
        if name in self._dispatchers:
            self._dispatchers[name](caller, e)
        
