# -*- coding: utf-8 -*-

__all__ = ['Profile']

from headstock.api.jid import JID
from headstock.api import Entity, Foreign
from headstock.api.dataform import Data, Field
from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_USER_PROFILE_NS, XMPP_DATA_FORM_NS

class Profile(Entity):
    def __init__(self, from_jid=None, to_jid=None, type=u'none', stanza_id=None):
        Entity.__init__(self, from_jid, to_jid, type=type, stanza_id=stanza_id)
        self.x = None

    def __repr__(self):
        return '<Profile %s at %s>' % (str(self.from_jid), hex(id(self)))

    @staticmethod
    def from_element(e):
        p = Profile(JID.parse(e.get_attribute_value('from')),
                    JID.parse(e.get_attribute_value('to')),
                    type=e.get_attribute_value('type', None),
                    stanza_id=e.get_attribute_value('id'))

        error = e.get_child('error', XMPP_CLIENT_NS)
        if error:
            registration.error = Error.from_element(error)

        profile = e.get_child('profile', XMPP_USER_PROFILE_NS)

        for c in profile.xml_children:
            if not isinstance(c, E):
                continue
            
            if c.xml_ns == XMPP_DATA_FORM_NS:
                p.x = Date.from_element(c)

        return p

    @staticmethod
    def to_element(e):
        iq = Entity.to_element(e)
        p = E(u'profile', namespace=XMPP_USER_PROFILE_NS, parent=iq)

        if e.x:
            Data.to_element(e.x, parent=p)

        return iq

    @staticmethod
    def to_profile_element(e):
        p = E(u'profile', namespace=XMPP_USER_PROFILE_NS)

        if e.x:
            Data.to_element(e.x, parent=p)

        return p

    @staticmethod
    def from_profile_element(e):
        p = Profile()

        for c in e.xml_children:
            if not isinstance(c, E):
                continue
            
            if c.xml_ns == XMPP_DATA_FORM_NS:
                p.x = Data.from_element(c)

        return p
