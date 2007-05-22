#!/usr/bin/env python
# -*- coding: utf-8 -*-

from headstock.lib.utils import generate_unique
from headstock.protocol.extension.si import SI
from headstock.protocol.core.jid import JID
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_SI_FILE_TRANSFER_NS, XMPP_BYTESTREAMS_NS

__all__ = ['SIManager', 'FileTransfer', 'FileTransferManager']

class FileTransfer(object):
    def __init__(self, request_id=None, mime_type=None, name=None,
                 size=None, date=None, hashvalue=None):
        self.request_id = request_id
        self.mime_type = mime_type
        self.name = name
        self.size = size
        self.date = date
        self.hash = hashvalue

    def __repr__(self):
        return '<FileTransfer "%s" at %s>' % (str(self.request_id), hex(id(self)))
        
class FileTransferManager(object):
    def __init__(self, session):
        self.session = session

    def requested(self, si, e):
        ft = e.get_child('file', XMPP_SI_FILE_TRANSFER_NS)
        file_transfer = FileTransfer(e.get_attribute('id'), e.get_attribute('mime-type'),
                                     ft.get_attribute('name'), ft.get_attribute('size'),
                                     ft.get_attribute('date'), ft.get_attribute('hash'))

##         to_jid = e.xml_parent.get_attribute('from')
##         iq = SI.create_accept_stream_initiation(unicode(self.session.stream.jid),
##                                                 to_jid, XMPP_BYTESTREAMS_NS,
##                                                 stanza_id=generate_unique())
##         self.session.stream.propagate(element=iq)
        
        to_jid = e.xml_parent.get_attribute('from')
        iq = SI.create_forbidden(unicode(self.session.stream.jid),
                                 to_jid, stanza_id=generate_unique())
        self.session.stream.propagate(element=iq)

class SIManager(object):
    def __init__(self):
        pass
