# -*- coding: utf-8 -*-

from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XML_PREFIX

from headstock.lib.utils import generate_unique

__all__ = ['Stanza']

class Stanza(object):
    """
    Helper class to create stanzas as :class:`bridge.Element` instance.

    ``name`` stanza element name

    ``from_jid`` JID emiting the stanza

    ``to_jid`` JID targeted by the stanza

    ``type`` stanza type (e.g. get, set, result)

    ``stanza_id`` stanza identifier

    ``lang`` xml:lang value
    """
    def __init__(self, name, from_jid=None, to_jid=None, type=None, stanza_id=None, lang=None):
        self.stanza = name
        self.from_jid = from_jid
        self.to_jid = to_jid
        self.type = type
        self.stanza_id = stanza_id or generate_unique()
        self.lang = lang

    def swap_jids(self):
        """
        Swap JID internally
        """
        self.from_jid, self.to_jid = self.to_jid, self.from_jid

    @staticmethod
    def to_element(e, parent=None):
        """
        Creates and returns a :class:`bridge.Element` instance from a
        :class:`headstock.lib.stanza.Stanza` instance.

        ``e`` :class:`headstock.lib.stanza.Stanza` instance

        ``parent`` :class:`bridge.Element` instance to which
        attached the generated element.
        """
        attributes = {}
        if e.type:
            attributes = {u'type': e.type}
        if e.from_jid:
            attributes[u'from'] = unicode(e.from_jid)
        if e.to_jid:
            attributes[u'to'] = unicode(e.to_jid)
        if e.type:
            attributes[u'type'] = e.type
        if e.stanza_id:
            attributes[u'id'] = e.stanza_id
            
        stanza = E(e.stanza, attributes=attributes, namespace=XMPP_CLIENT_NS,
                   parent=parent)
        
        if e.lang:
            A(u'lang', value=e.lang, prefix=XML_PREFIX,
              namespace=XML_NS, parent=stanza)

        return stanza

    @staticmethod
    def get_iq(from_jid=None, to_jid=None, stanza_id=None):
        """
        Helper method that generates a :class:`headstock.lib.stanza.Stanza` instance
        of a IQ stanza with a `get` type.
        """
        return Stanza.to_element(Stanza(u'iq', from_jid=from_jid, to_jid=to_jid, type=u'get',
                                        stanza_id=stanza_id))

    @staticmethod
    def set_iq(from_jid=None, to_jid=None, stanza_id=None):
        """
        Helper method that generates a :class:`headstock.lib.stanza.Stanza` instance
        of a IQ stanza with a `set` type.
        """
        return Stanza.to_element(Stanza(u'iq', from_jid=from_jid, to_jid=to_jid,
                                        type=u'set', stanza_id=stanza_id))

    @staticmethod
    def result_iq(self, from_jid=None, to_jid=None, stanza_id=None):
        """
        Helper method that generates a :class:`headstock.lib.stanza.Stanza` instance
        of a IQ stanza with a `result` type.
        """
        return Stanza.to_element(Stanza(u'iq', from_jid=from_jid, to_jid=to_jid,
                                        type=u'result', stanza_id=stanza_id))
    
    @staticmethod
    def error_iq(from_jid=None, to_jid=None, stanza_id=None):
        """
        Helper method that generates a :class:`headstock.lib.stanza.Stanza` instance
        of a IQ stanza with a `error` type.
        """
        return Stanza.to_element(Stanza(u'iq', from_jid=from_jid, to_jid=to_jid,
                                        type=u'error', stanza_id=stanza_id))
