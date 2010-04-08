# -*- coding: utf-8 -*-
import headstock
from headstock.lib.stanza import Stanza
from headstock.error import HeadstockAvailable
from bridge import Element as E
from bridge import Attribute as A
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS

class Basic(object):
    def ready(self, client):
        self.client = client

    def cleanup(self):
        self.client = None
        
    @headstock.xmpphandler('item', XMPP_ROSTER_NS)
    def roster(self, e):
        self.client.log("Contact '%s' %s with subscription: %s" % (e.get_attribute_value('name', ''),
                                                                   e.get_attribute_value('jid', ''),
                                                                   e.get_attribute_value('subscription', '')))

    @headstock.xmpphandler('presence', XMPP_CLIENT_NS)
    def presence(self, e):
        if not hasattr(self, "client"):
            raise HeadstockAvailable()
        self.client.log("Received '%s' presence from: %s" % (e.get_attribute_value('type', 'available'),
                                                             e.get_attribute_value('from')))

    @headstock.xmpphandler('message', XMPP_CLIENT_NS)
    def message(self, e):
        who = e.get_attribute_value('from')
        body = e.get_child('body', ns=e.xml_ns)
        print "%s says: %s" % (who, body.xml_text)

        # Echo the received message
        m = E(u"message", attributes={u'from': unicode(self.client.jid), u'to': who, u'type': u'chat',
                                      u'id': e.get_attribute_value('id')},
              namespace=XMPP_CLIENT_NS)
        E(u'body', content=body.xml_text, namespace=XMPP_CLIENT_NS, parent=m)
        
        self.client.send_stanza(m)

if __name__ == '__main__':
    from headstock.lib.utils import parse_commandline
    
    options = parse_commandline()
    if not options.password:
        from getpass import getpass
        options.password = getpass()
    host, port = options.address.split(':')

    registercls = None
    if options.register:
        from headstock.register import Register
        registercls = Register
    
    from headstock.client import AsyncClient
    c = AsyncClient(unicode(options.jid), unicode(options.password),
                    hostname=host, port=int(port), tls=options.usetls,
                    registercls=registercls)
    c.set_log(stdout=True)
    
    c.register(Basic())

    c.run()
