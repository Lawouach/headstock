#!/usr/bin/env python
# -*- coding: utf-8 -*-


__all__ = ['Rpc']

import xmlrpclib

from headstock.lib.utils import generate_unique
from headstock.protocol.core.jid import JID
from headstock.protocol.core.iq import Iq
from headstock.protocol.extension.rpc import RPC
from bridge.common import XMPP_RPC_NS
from bridge import Element as E
from bridge import ENCODING

class Rpc(object):
    def __init__(self, session):
        self.session = session
        self.method_called = None
        self.error_raised = None

    def on_method_called(self, handler):
        self.error_raised = handler

    def on_error_raised(self, handler):
        self.error_raised = handler

    def call(self, to_jid, method_name, params, encoding=ENCODING):
        payload = xmlrpclib.dumps(params, methodname=method_name,
                                  encoding=encoding, allow_none=False)
        iq = RPC.create_method_call(unicode(self.session.stream.jid), to_jid, payload)
        self.session.stream.propagate(element=iq)

    def send_fault(self, message):
        payload = xmlrpclib.dumps(xmlrpclib.Fault(1, message))
        iq = RPC.create_method_call(unicode(self.session.stream.jid), to_jid, payload)
        self.session.stream.propagate(element=iq)

    def called(self, rpc, e):
        if not callable(self.method_called):
            return
        method_call = e.get_child('methodCall', XMPP_RPC_NS)
        try:
            params, method_name = xmlrpclib.loads(method_call.xml(omit_declaration=True))
            self.method_called(method_name, params)
        except xmlrpclib.Fault, x:
            if callable(self.error_raised):
                self.error_raised(x.faultCode, x.faultString)
