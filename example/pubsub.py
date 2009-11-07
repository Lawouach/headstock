# -*- coding: utf-8 -*-
import headstock
from headstock.client import AsyncClient
from headstock.lib.stanza import Stanza
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS,\
     XMPP_PUBSUB_NS

from basic import Basic

class PubSub(object):
    def ready(self, client):
        self.client = client
        self.fetch()
        self.unsubscribe(u"http://www.reddit.com/r/WeAreTheMusicMakers/.rss")
        self.subscribe(u"http://www.reddit.com/r/WeAreTheMusicMakers/.rss")

    def fetch(self):
        iq = Stanza.get_iq(self.client.jid, u"firehoser.superfeedr.com")
        
        pubsub = E(u"pubsub", namespace=XMPP_PUBSUB_NS, parent=iq)
        A(u"superfeedr", prefix=u"xmlns", parent=pubsub,
          namespace=u"http://superfeedr.com/xmpp-pubsub-ext")
        sub = E(u"subscriptions", attributes={u"jid": unicode(self.client.jid)},
                parent=pubsub, namespace=XMPP_PUBSUB_NS)
        A(u"page", value=u"1", prefix=u"superfeedr", parent=sub)

        self.client.send_stanza(iq)
        
    def subscribe(self, url):
        iq = Stanza.set_iq(self.client.jid, u"firehoser.superfeedr.com")
        
        pubsub = E(u"pubsub", namespace=XMPP_PUBSUB_NS, parent=iq)
        A(u"superfeedr", prefix=u"xmlns", parent=pubsub,
          namespace=u"http://superfeedr.com/xmpp-pubsub-ext")
        E(u"subscribe", attributes={u"jid": u"", u"node": url},
                parent=pubsub, namespace=XMPP_PUBSUB_NS)

        self.client.send_stanza(iq)

    def unsubscribe(self, url):
        iq = Stanza.set_iq(self.client.jid, u"firehoser.superfeedr.com")
        
        pubsub = E(u"pubsub", namespace=XMPP_PUBSUB_NS, parent=iq)
        A(u"superfeedr", prefix=u"xmlns", parent=pubsub,
          namespace=u"http://superfeedr.com/xmpp-pubsub-ext")
        E(u"unsubscribe", attributes={u"jid": u"", u"node": url},
                parent=pubsub, namespace=XMPP_PUBSUB_NS)

        self.client.send_stanza(iq)

    @headstock.xmpphandler('subscription', XMPP_PUBSUB_NS)
    def subscription(self, e):
        print e.xml()

    @headstock.xmpphandler('message', XMPP_PUBSUB_NS)
    def message(self, e):
        print e.xml()


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
