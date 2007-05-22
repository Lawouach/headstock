#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['VersionInfo', 'VersionManager']

from headstock.lib.utils import generate_unique
from headstock.protocol.extension.version import Version
from headstock.protocol.core.jid import JID
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_VERSION_NS

class VersionInfo(object):
    def __init__(self, name, version, os=None):
        self.name = name
        self.version = version
        self.os = os

    def __repr__(self):
        return '<VersionInfo %s (%s) on %s at %s>' % (self.name, self.version,
                                                      self.os or 'N/A', hex(id(self)))


class VersionManager(object):
    def __init__(self, session):
        self.session = session
        self.version_info = None
        self.version_info_received = None

    def on_received(self, handler):
        self.version_info_received = handler

    def set(self, info):
        self.version_info = info

    def requested(self, version, e):
        if self.version_info:
            self.send(unicode(e.xml_parent.get_attribute('from')),
                      self.version_info)

    def send(self, to_jid, info):
        iq = Version.create_version_response(unicode(self.session.stream.jid),
                                             to_jid, info.name, info.version, info.os,
                                             stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)
        
    def received(self, version, e):
        if callable(self.version_info_received):
            self.version_info_received(VersionInfo(e.get_child('name', XMPP_VERSION_NS),
                                                   e.get_child('version', XMPP_VERSION_NS),
                                                   e.get_child('os', XMPP_VERSION_NS)))

    def ask(self, to_jid):
        iq = Version.create_version_request(unicode(self.session.stream.jid),
                                            to_jid, stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)
