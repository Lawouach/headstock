# -*- coding: utf-8 -*-

__all__ = ['BaseStorage', 'NullStorage',
           'Entity', 'Contact', 'Group', 'Resource', 'Tracker']

class BaseStorage(object):
    def set_logger(self, logger=None):
        raise NotImplemented

    def reset(self):
        raise NotImplemented

    def save(self, obj, **kwargs):
        raise NotImplemented
    

class NullStorage(BaseStorage):
    def set_logger(self, logger=None):
        pass
    
    def reset(self):
        pass

    def save(self, obj, **kwargs):
        pass

##############################################################
# Mapping to the storage entities
# They must be implemented in each storage kind
##############################################################

import sys

if sys.platform == 'cli': # IronPython
    raise NotImplemented
else: # CPython
    from headstock.api.storage.dejavu_provider import Entity, \
         Contact, Group, Resource, Tracker
    
