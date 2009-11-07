#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bridge.filter.xmpp import lookup_first_error

__all__ = ['Error', 'HeadstockError', 'HeadstockInvalidError',
           'HeadstockStreamError', 'HeadstockAuthenticationFailure',
           'HeadstockInvalidStanzaError', 'HeadstockAuthenticationSuccess',
           'HeadstockSessionBound', 'HeadstockStartTLS']

class Error(object):
    _error_mapping = {'failure': 'failure', 'conflict': 'conflict'}

    def __init__(self, registry):
        self.registry = registry

    def apply_error_handler(self, element, response, *args, **kwargs):
        if element.xml_name in self.registry:
            handler_name = Error._error_mapping[element.xml_name]
            self.registry.run(handler_name, element, response, *args, **kwargs)

    def lookup(self, element):
        return element.filtrate(lookup_first_error)

class HeadstockError(StandardError):
    pass

class HeadstockInvalidError(HeadstockError):
    pass

class HeadstockStreamError(HeadstockError):
    pass

class HeadstockAuthenticationFailure(HeadstockError):
    pass

class HeadstockAuthenticationSuccess(HeadstockError):
    pass

class HeadstockInvalidStanzaError(HeadstockError):
    pass

class HeadstockSessionBound(HeadstockError):
    pass

class HeadstockStartTLS(HeadstockError):
    pass
