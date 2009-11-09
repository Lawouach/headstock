# -*- coding: utf-8 -*-

import re
try:
    import hashlib
    HASH = lambda x: hashlib.sha1(x).hexdigest()
except ImportError:
    import sha
    HASH = lambda x: sha.new(x).hexdigest()
    
# taken from http://code.sixapart.com/cgi-bin/viewcvs.cgi/trunk/DJabberd/lib/DJabberd/JID.pm?rev=684&view=markup
_r_jid = re.compile(u'(?:([\x29\x23-\x25\x28-\x2E\x30-\x39\x3B\x3D\x3F\x41-\x7E]{1,1023})\@)?([a-zA-Z0-9\.\-]{1,1023})(?:/(.{1,1023}))?', re.UNICODE)

class JID(object):
    """
    Jabber Identifier helper class.

    ``node`` JID node part

    ``domain`` JID domain part

    ``resource`` None - JID resource
    """
    def __init__(self, node, domain, resource=None):
        self.node = node
        self.domain = domain
        self.resource = resource

    @staticmethod
    def parse(token):
        """
        Parses a string representing a JID and returns
        an instance of :class:`headstock.lib.jid.JID` or
        `None` if it failed.
        """
        if not token:
            return
        m = _r_jid.match(token)
        if m is not None:
            node, domain, resource = m.groups()
            return JID(node, domain, resource)

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

    def domainid(self):
        return self.domain

    def nodeid(self):
        if self.node and self.domain:
            return "%s@%s" % (self.node, self.domain)
        return self.domain

    def ressourceid(self):
        if self.node and self.domain and self.resource:
            return "%s@%s/%s" % (self.node, self.domain, self.resource)
        return self.domain
      
    @property
    def hashed(self):
        """
        Returns a sha1 hash of of the JID.
        """
        return HASH(str(self))
