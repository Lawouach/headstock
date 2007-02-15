#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

# taken from http://code.sixapart.com/cgi-bin/viewcvs.cgi/trunk/DJabberd/lib/DJabberd/JID.pm?rev=684&view=markup
_r_jid = re.compile(u'(?:([\x29\x23-\x25\x28-\x2E\x30-\x39\x3B\x3D\x3F\x41-\x7E]{1,1023})\@)?([a-zA-Z0-9\.\-]{1,1023})(?:/(.{1,1023}))?', re.UNICODE)

class JID(object):
    def __init__(self, node, domain, resource):
        self.node = node
        self.domain = domain
        self.resource = resource

    @classmethod
    def parse(cls, token):
        m = _r_jid.match(token)
        if m is not None:
            node, domain, resource = m.groups()
            return JID(node, domain, resource)
        return None

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

    def __repr__(self):
        return '<jid %s>' % self.__str__()
