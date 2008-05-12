#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bridge import Element as E
from bridge.common import XMPP_DATA_FORM_NS

__all__ = ['Data', 'Field', 'Option', 'Item']

class Data(object):
    def __init__(self, form_type, reported=False):
        self.type = form_type
        self.reported = reported
        self.instructions = None
        self.title = None
        self.fields = []
        self.items = []

    def __repr__(self):
        return '<Data "%s" at %s>' % (self.type, hex(id(self)))

    def field_by_var(self, var):
        for field in self.fields:
            if field.var == var:
                return field
    
    @staticmethod
    def from_element(e):
        d = Data(e.get_attribute_value('type'))
        title = e.get_child('title', e.xml_ns)
        if title:
            d.title = title.xml_text

        instructions = e.get_child('instructions', e.xml_ns)
        if instructions:
            d.instructions = instructions.xml_text

        fields = e.get_children('field', e.xml_ns)
        for field in fields:
            d.fields.append(Field.from_element(field))

        items = e.get_children('item', e.xml_ns)
        for item in items:
            d.items.append(Item.from_element(item))

        return d

    @staticmethod
    def to_element(d, parent=None):
        x = E(u'x', attributes={u'type': d.type},
              namespace=XMPP_DATA_FORM_NS, parent=parent)
        for field in d.fields:
            Field.to_element(field, parent=x)
        for item in d.items:
            Item.to_element(item, parent=x)
                   
class Field(object):
    def __init__(self, required=False, field_type=u'text-single', var=None, values=None):
        self.required = required
        self.type = field_type
        self.var = var
        self.label = None
        self.desc = None
        self.options = []
        self.values = values or []
        
    def __repr__(self):
        return '<Field "%s" (%s) at %s>' % (self.type or '', self.var or '', hex(id(self)))
    
    @staticmethod
    def from_element(e):
        f = Field(field_type=e.get_attribute_value('type'),
                  var=e.get_attribute_value('var'))
        f.label = e.get_attribute_value('label')
        required = e.get_child('required', e.xml_ns)
        if required and required == 'true':
            f.required = True
        desc = e.get_child('desc', e.xml_ns)
        if desc:
            f.desc = desc.xml_text

        options = e.get_children('option', e.xml_ns)
        for option in options:
            f.options.append(Option.from_element(option))

        values = e.get_children('value', e.xml_ns)
        for value in values:
            f.values.append(value.xml_text)

        return f

    @staticmethod
    def to_element(field, parent=None):
        attrs = {}
        if field.var: attrs[u'var'] = field.var
        if field.type: attrs[u'type'] = field.type
        f = E(u'field', attributes=attrs,
              namespace=XMPP_DATA_FORM_NS, parent=parent)
        for value in field.values:
            E(u'value', content=value,
              namespace=XMPP_DATA_FORM_NS, parent=f)
    
class Option(object):
    def __init__(self, value, label=None):
        self.value = value
        self.label = label
        
    def __repr__(self):
        return '<Option "%s" at %s>' % (self.value, hex(id(self)))
    
    @staticmethod
    def from_element(e):
        o = Option(e.get_child('value', e.xml_ns).xml_text,
                   e.get_attribute_value('label'))
        return o

    @staticmethod
    def to_element(e, parent=None):
        option = E(u'option', namespace=XMPP_DATA_FORM_NS, 
                   attributes={u'label': e.label}, parent=parent)
        E(u'value', namespace=XMPP_DATA_FORM_NS, 
          content=e.value, parent=option)
        return option

        
class Item(object):
    def __init__(self):
        self.fields = []

    def __repr__(self):
        return '<Item at %s>' % (hex(id(self)),)
    
    @staticmethod
    def from_element(e):
        i = Item()
        fields = e.get_children('field', e.xml_ns)
        for field in fields:
            i.fields.append(Field.from_element(field))

        return i

    @staticmethod
    def to_element(e, parent=None):
        item = E(u'item', namespace=XMPP_DATA_FORM_NS, parent=parent)
        for field in e.fields:
            Field.to_element(field, parent=item)
        return item
