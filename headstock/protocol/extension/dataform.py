#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.error import HeadstockInvalidError

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_DATA_FORM_NS

__all__ = ['Field', 'Option', 'DataForm']

class Field(object):
    def __init__(self, var=None, type=None, label=None, required=False, description=None):
        self.var = var
        self.type = type
        self.label = label
        self.required = required
        self.description = description
        self.values = []
        self.options = []

    def xml(self):
        return self.to_bridge().xml(omit_declaration=True)

    def to_bridge(self, parent=None):
        field = E('field', namespace=XMPP_DATA_FORM_NS, parent=parent)

        type = self.type
        if self.values and not self.type:
            # see section 3.2
            type =  u'text-single'
            
        A('type', value=type, parent=field)

        if type != 'fixed' and not self.var:
            # see section 3.2
            raise HeadstockInvalidError, "Missing 'var' value"

        if self.var:
            A('var', value=self.var, parent=field)
            
        if self.label:
            A('label', value=self.label, parent=field)

        if self.required:
            E('required', namespace=XMPP_DATA_FORM_NS, parent=field)
        
        if self.description:
            E('desc', content=self.description.replace('\n', ' ').replace('\r', ' '),
              namespace=XMPP_DATA_FORM_NS, parent=field)
            
        for value in self.values:
            E('value', content=value,
              namespace=XMPP_DATA_FORM_NS, parent=field)

        # see section 3.2
        if self.type in ['list-single', 'list-multi']:
            for option in self.options:
                option.to_bridge(parent=field)

        return field
        
class Option(object):
    def __init__(self, label=None, value=None):
        self.label = label
        self.values = value

    def xml(self):
        return self.to_bridge().xml(omit_declaration=True)

    def to_bridge(self, parent=None):
        option = E('option', namespace=XMPP_DATA_FORM_NS, parent=parent)

        if self.label:
            A('label', value=self.label, parent=option)

        if self.value:
            E('value', content=self.value,
              namespace=XMPP_DATA_FORM_NS, parent=option)

        return option

class DataForm(object):
    def __init__(self, type, title=None):
        if not type:
            raise "DataForm requires a type"
        self.type = type
        self.title = title
        self.instructions = []
        self.fields = []
        self.items = []
        
    def xml(self):
        return self.to_bridge().xml(omit_declaration=True)

    def to_bridge(self, parent=None):
        x = E('x', attributes={u'type': self.type},
              namespace=XMPP_DATA_FORM_NS, parent=parent)
        
        if self.title:
            E('title', content=self.title, parent=x,
              namespace=XMPP_DATA_FORM_NS)

        for instruction in self.instructions:
            E('instructions', content=instruction, parent=x,
              namespace=XMPP_DATA_FORM_NS)

        for field in self.fields:
            field.to_bridge(parent=x)

        for item in self.items:
            item.to_bridge(parent=x)

        return x
