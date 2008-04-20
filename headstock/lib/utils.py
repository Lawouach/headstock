#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sha
from time import time
from random import random

from bridge.common import XML_NS, XMPP_CLIENT_NS
from headstock.error import HeadstockInvalidStanzaError
from headstock.protocol.core.stanza import Stanza

__all__ = ['generate_unique', 'validate_iq_stanza',
           'extract_from_stanza']

def generate_unique(seed=None):
    if not seed:
        seed = str(time() * random())
    return unicode(abs(hash(sha.new(seed).hexdigest())))

def extract_from_stanza(e):
    stanza = None
    if e.xml_name in ['iq', 'presence', 'message']:
        stanza = e
    elif e.xml_parent.xml_name in ['iq', 'presence', 'message']:
        stanza = e.xml_parent

    if not stanza or (stanza.xml_ns != XMPP_CLIENT_NS):
        return
    
    st = Stanza()

    st.kind = stanza.xml_name
    
    id = stanza.get_attribute('id')
    if id:
        st.id = unicode(id)

    from_jid = stanza.get_attribute('from')
    if from_jid:
        st.from_jid = unicode(from_jid)
        
    from_jid = stanza.get_attribute('from')
        
    st_type = stanza.get_attribute('type')
    if st_type:
        st.type = unicode(st_type)

    to_jid = stanza.get_attribute('to')
    if to_jid:
        st.to_jid = unicode(to_jid)

    lang = stanza.get_attribute_ns('lang', XML_NS)
    if lang:
        st.lang = unicode(lang)

    print repr(st)
    st.children.extend(stanza.xml_children)
    return st

# see section 9.2.3 of RFC 3920
def validate_iq_stanza(e):
    iq = e
    if e.xml_parent.xml_name == 'iq':
        iq = e.xml_parent
    
    # The 'id' attribute is REQUIRED for IQ stanzas.
    if not iq.get_attribute('id'):
        raise HeadstockInvalidStanzaError("Missing 'id' attribute")

    # The 'type' attribute is REQUIRED for IQ stanzas.
    # The value MUST be one of the following: get, set, error, result
    stanza_type = iq.get_attribute('type')
    if not stanza_type:
        raise HeadstockInvalidStanzaError("Missing 'type' attribute")

    stanza_type = str(stanza_type)
    if stanza_type not in ['get', 'set', 'result', 'error']:
        raise HeadstockInvalidStanzaError("Wrong 'type' attribute value: '%s'" % stanza_type)

    # An IQ stanza of type "get" or "set" MUST contain one and only one
    # child element that specifies the semantics of the
    # particular request or response.
    if (stanza_type in ['get', 'set']) and (len(iq.xml_children) != 1):
        raise HeadstockInvalidStanzaError("Stanza must have exactly one child")

    # An IQ stanza of type "result" MUST include zero or one child elements.
    if (stanza_type == 'result') and (len(iq.xml_children) > 1):
        raise HeadstockInvalidStanzaError("Cannot have more than several children in stanza")

    
 
