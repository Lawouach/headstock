#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bridge import Element as E
from bridge.common import XMPP_DATA_FORM_NS

__all__ = ['Data', 'Field', 'Option', 'Item']

class Data(object):
    def __init__(self, form_type, reported=False):
        self.type = form_type
        self.reported = reported
        self.title = None
        self.fields = []
        self.items = []

    def __repr__(self):
        return '<Data "%s" at %s>' % (self.type, hex(id(self)))
    
    def from_element(cls, e):
        d = Data(unicode(e.get_attribute('type')))
        title = e.get_child('title', e.xml_ns)
        if title:
            d.title = title.xml_text

        fields = e.get_children('field', e.xml_ns)
        for field in fields:
            d.fields.append(Field.from_element(field))

        items = e.get_children('item', e.xml_ns)
        for item in items:
            d.items.append(Item.from_element(item))

        return d
    from_element = classmethod(from_element)

    def to_element(cls, d, parent=None):
        x = E(u'x', attributes={u'type': d.type},
              namespace=XMPP_DATA_FORM_NS, parent=parent)
        for field in d.fields:
            Field.to_element(field, parent=x)
    to_element = classmethod(to_element)
                   
class Field(object):
    def __init__(self, required=False, field_type=u'text-single', var=None):
        self.required = required
        self.type = field_type
        self.var = var
        self.label = None
        self.desc = None
        self.options = []
        self.values = []
        
    def __repr__(self):
        return '<Field "%s" (%s) at %s>' % (self.type or '', self.var or '', hex(id(self)))
    
    def from_element(cls, e):
        f = Field()
        f.type = e.get_attribute('type')
        f.var = e.get_attribute('var')
        f.label = e.get_attribute('label')
        required = e.get_child('required')
        if required and required == 'true':
            f.required = True
        desc = e.get_child('desc')
        if desc:
            f.desc = desc.xml_text

        options = e.get_children('option', e.xml_ns)
        for option in options:
            f.options.append(Option.from_element(option))

        values = e.get_children('value', e.xml_ns)
        for value in values:
            f.values.append(value.xml_text)

        return f
    from_element = classmethod(from_element)

    def to_element(cls, field, parent=None):
        attrs = {}
        if field.var: attrs[u'var'] = field.var
        if field.type: attrs[u'type'] = field.type
        f = E(u'field', attributes=attrs,
              namespace=XMPP_DATA_FORM_NS, parent=parent)
        for value in field.values:
            E(u'value', content=value,
              namespace=XMPP_DATA_FORM_NS, parent=f)
    to_element = classmethod(to_element)
    
class Option(object):
    def __init__(self, value, label=None):
        self.value = value
        self.label = label
        
    def __repr__(self):
        return '<Option "%s" at %s>' % (self.value, hex(id(self)))
    
    def from_element(cls, e):
        o = Option()
        o.value = e.get_child('value').xml_text
        label = e.get_child('label')
        if label:
            o.label = label.xml_text
        return o
    from_element = classmethod(from_element)

class Item(object):
    def __init__(self):
        self.fields = []

    def __repr__(self):
        return '<Item at %s>' % (hex(id(self)),)
    
    def from_element(cls, e):
        i = Item()
        fields = e.get_children('field', e.xml_ns)
        for field in fields:
            i.fields.append(Field.from_element(field))

        return i
    from_element = classmethod(from_element)
