#!/usr/bin/env python
# -*- coding: utf-8 -*-

class JID(object):
    def __init__(self, node, domain, resource):
        self.node = node
        self.domain = domain
        self.resource = resource

    def parse(cls, token):
        pass
    parse = classmethod(parse)

    def __str__(self):
        if self.node and self.domain and self.resource:
            return "%s@%s/%s" % (self.node, self.domain, self.resource)
        elif self.node and self.domain:
            return "%s@%s" % (self.node, self.domain)
        elif self.domain and self.resource:
            return "%s/%s" % (self.domain, self.resource)
        elif self.domain:
            return self.domain

    def __unicode__(self):
        value = self.__str__()
        return value.decode('utf-8')
