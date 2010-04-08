# -*- coding: utf-8 -*-
import headstock
from headstock.client import AsyncClient
from headstock.lib.stanza import Stanza
from headstock.lib.utils import generate_unique
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS,\
     XMPP_PUBSUB_NS, XMPP_DISCO_ITEMS_NS, XMLNS_NS, \
     XMPP_PUBSUB_EVENT_NS, ATOM10_NS

from basic import Basic

URL = u"http://twitter.com/#search?q=XMas"

class PubSub(object):
    def ready(self, client):
        self.client = client
        self.unsubscribe()

    def fetch(self, e):
        stanza_id = generate_unique()
        iq = Stanza.get_iq(self.client.jid, u"firehoser.superfeedr.com",
                           stanza_id=stanza_id)
        
        pubsub = E(u"pubsub", namespace=XMPP_PUBSUB_NS, parent=iq)
        A(u"superfeedr", prefix=u"xmlns", namespace=XMLNS_NS, parent=pubsub,
          value=u"http://superfeedr.com/xmpp-pubsub-ext")
        sub = E(u"subscriptions", attributes={u"jid": unicode(self.client.jid)},
                parent=pubsub, namespace=XMPP_PUBSUB_NS)
        A(u"page", value=u"1", prefix=u"superfeedr", parent=sub,
          namespace=u"http://superfeedr.com/xmpp-pubsub-ext")

        self.client.register_on_iq(self.subscriptions, type="result", id=stanza_id, once=True)
        self.client.send_stanza(iq)

    def subscriptions(self, e):
        iq = Stanza.get_iq(self.client.jid, u"firehoser.superfeedr.com")
        E(u"query", namespace=XMPP_DISCO_ITEMS_NS, parent=iq)
        self.client.send_stanza(iq)
        
    def subscribe(self, e):
        print "bog"
        stanza_id = generate_unique()
        iq = Stanza.set_iq(self.client.jid, u"firehoser.superfeedr.com",
                           stanza_id=stanza_id)
        
        pubsub = E(u"pubsub", namespace=XMPP_PUBSUB_NS, parent=iq)
        A(u"superfeedr", prefix=u"xmlns", namespace=XMLNS_NS, parent=pubsub,
          value=u"http://superfeedr.com/xmpp-pubsub-ext")
        E(u"subscribe", attributes={u"jid": self.client.jid.nodeid(),
                                    u"node": URL},
          parent=pubsub, namespace=XMPP_PUBSUB_NS)

        self.client.register_on_iq(self.fetch, type="result",
                                   id=stanza_id, once=True)
        self.client.send_stanza(iq)

    def unsubscribe(self, url=URL):
        stanza_id = generate_unique()
        iq = Stanza.set_iq(self.client.jid, u"firehoser.superfeedr.com",
                           stanza_id=stanza_id)
        
        pubsub = E(u"pubsub", namespace=XMPP_PUBSUB_NS, parent=iq)
        A(u"superfeedr", prefix=u"xmlns", namespace=XMLNS_NS, parent=pubsub,
          value=u"http://superfeedr.com/xmpp-pubsub-ext")
        E(u"unsubscribe", attributes={u"jid": self.client.jid.nodeid(),
                                      u"node": url},
          parent=pubsub, namespace=XMPP_PUBSUB_NS)

        self.client.register_on_iq(self.subscribe, type="result",
                                   id=stanza_id, once=True)
        self.client.send_stanza(iq)

    @headstock.xmpphandler('subscription', XMPP_PUBSUB_NS)
    def subscription(self, e):
        iq = Stanza.get_iq(self.client.jid, u"firehoser.superfeedr.com")
        E(u"query", namespace=XMPP_DISCO_ITEMS_NS, parent=iq,
          attributes={u'node': e.get_attribute_value('node')})
        self.client.send_stanza(iq)

    @headstock.xmpphandler('entry', ATOM10_NS)
    def entry(self, e):
        print e.get_child('title', ns=ATOM10_NS).xml_text

    @headstock.xmpphandler('message', XMPP_CLIENT_NS)
    def message(self, e):
        pass

if __name__ == '__main__':
    from headstock.lib.utils import parse_commandline
    
    options = parse_commandline()
    if not options.password:
        from getpass import getpass
        options.password = getpass()
    host, port = options.address.split(':')
    
    c = AsyncClient(unicode(options.jid), unicode(options.password),
                    hostname=host, port=int(port), tls=options.usetls)
    c.set_log(stdout=True)
    
    c.register(Basic())
    c.register(PubSub())

    c.run()
