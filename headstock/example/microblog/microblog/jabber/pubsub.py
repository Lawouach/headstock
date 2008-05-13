# -*- coding: utf-8 -*-
from Axon.Component import component
from Kamaelia.Util.Backplane import PublishTo, SubscribeTo
from Axon.Ipc import shutdownMicroprocess, producerFinished
    
from headstock.api.jid import JID
from headstock.api.im import Message, Body
from headstock.api.pubsub import Node, Item, Message
from headstock.api.discovery import *
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS, \
    XMPP_LAST_NS, XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS,\
    XMPP_PUBSUB_NS

from amplee.utils import extract_url_trail, get_isodate,\
    generate_uuid_uri
from amplee.error import ResourceOperationException

from microblog.web.atompub import ResourceWrapper

__all__ = ['DiscoHandler', 'ItemsHandler', 'MessageHandler']

class DiscoHandler(component):
    Inboxes = {"inbox"       : "",
               "control"     : "", 
               "initiate"    : "",
               "jid"         : "",
               "features.result": "",
               "items.result": "",
               "items.error" : "",
               "subscriptions.result": ""}
    
    Outboxes = {"outbox"        : "",
                "signal"        : "Shutdown signal",
                "features-disco": "headstock.api.discovery.FeaturesDiscovery query to the server",   
                "features-announce": "headstock.api.discovery.FeaturesDiscovery informs"\
                    "the other components about the features instance received from the server",
                "items-disco"   : "",
                "create-node"   : "",
                "subscribe-node"   : "",
                "subscriptions-disco": ""}

    def __init__(self, from_jid, atompub, host='localhost'):
        super(DiscoHandler, self).__init__() 
        self.from_jid = from_jid
        self.atompub = atompub
        self.xmpphost = host

    def initComponents(self):
        sub = SubscribeTo("JID")
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        pub = PublishTo("DISCO_FEAT")
        self.link((self, 'features-announce'), (pub, 'inbox'))
        self.addChildren(pub)
        pub.activate()

        sub = SubscribeTo("BOUND")
        self.link((sub, 'outbox'), (self, 'initiate'))
        self.addChildren(sub)
        sub.activate()

        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')
            
            if self.dataReady("initiate"):
                self.recv("initiate")
                
                d = FeaturesDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost)
                self.send(d, "features-disco")

                d = SubscriptionsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost)
                self.send(d, "subscriptions-disco")
                
                n = ItemsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost, 
                                   node_name=u'home/%s' % (self.xmpphost, ))
                self.send(n, "items-disco")

            # The response to our discovery query
            # is a a headstock.api.discovery.FeaturesDiscovery instance.
            # What we immediatly do is to notify all handlers
            # interested in that event about it.
            if self.dataReady('features.result'):
                disco = self.recv('features.result')
                print "Supported features:"
                for feature in disco.features:
                    print "  ", feature.var
                self.send(disco, 'features-announce')

            if self.dataReady('items.result'):
                items_disco = self.recv('items.result')
                print "%s has %d item(s)" % (items_disco.node_name, len(items_disco.items))
                
                for item in items_disco.items:
                    c = self.atompub.retrieve_collection(item.node) 
                    if c:
                        p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                                 node_name=item.node, sub_jid=self.from_jid.nodeid())
                        self.send(p, "subscribe-node")
                    
                        n = ItemsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost, 
                                           node_name=item.node)
                        self.send(n, "items-disco")
                        yield 1

            if self.dataReady('items.error'):
                items_disco = self.recv('items.error')
                print items_disco.node_name, items_disco.error

                if items_disco.error.condition == 'item-not-found':
                    p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                             node_name=items_disco.node_name)
                    self.send(p, "create-node")
                    yield 1                    
                
            if self.dataReady('subscriptions.result'):
                subscriptions = self.recv('subscriptions.result')
                print "You have %d subscription(s)" % (len(subscriptions.subscriptions),)

            if not self.anyReady():
                self.pause()
  
            yield 1

class ItemsHandler(component):
    Inboxes = {"inbox"      : "",
               "control"    : "", 
               "xmpp.result": "",
               "jid"        : "",}
    
    Outboxes = {"outbox"  : "",
                "publish" : "",
                "delete"  : "",
                "signal"  : "Shutdown signal",}

    def __init__(self, from_jid, atompub, host='localhost'):
        super(ItemsHandler, self).__init__() 
        self.from_jid = from_jid
        self.atompub = atompub
        self.xmpphost = host

    def initComponents(self):
        sub = SubscribeTo("JID")
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        return 1

    def make_entry(self, msg):
        uuid = generate_uuid_uri()
        entry = E.load('./entry.atom').xml_root
        entry.get_child('id', ns=entry.xml_ns).xml_text =  uuid
        dt = get_isodate()
        entry.get_child('published', ns=entry.xml_ns).xml_text = dt
        entry.get_child('updated', ns=entry.xml_ns).xml_text = dt
        entry.get_child('content', ns=entry.xml_ns).xml_text = unicode(msg)
        return uuid, entry
        
    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')
            
            if self.dataReady("inbox"):
                data = self.recv("inbox")
                if isinstance(data, str):
                    data = data.strip()
                    if data and data.startswith('publish:'):
                        node, msg = data.split('publish:')[1].strip().split(' ', 1)
                    
                        uuid, entry = self.make_entry(msg)
                        i = Item(id=uuid, payload=entry)
                        p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                                 node_name=unicode(node.strip()), item=i)
                        self.send(p, "publish")
                        yield 1
                    elif data and data.startswith('delete:'):
                        node, item_id = data.split('delete:')[1].strip().split(' ', 1)
                    
                        i = Item(id=unicode(item_id))
                        p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                                 node_name=unicode(node.strip()), item=i)
                        self.send(p, "delete")
                        yield 1

            if not self.anyReady():
                self.pause()
  
            yield 1

class MessageHandler(component):
    Inboxes = {"inbox"      : "",
               "control"    : "",
               "jid"        : "",}
    
    Outboxes = {"outbox"  : "",
                "signal"  : "Shutdown signal",
                "items-disco"   : "",}

    def __init__(self, from_jid, atompub, host='localhost'):
        super(MessageHandler, self).__init__() 
        self.from_jid = from_jid
        self.atompub = atompub
        self.xmpphost = host

    def initComponents(self):
        sub = SubscribeTo("JID")
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')
            
            if self.dataReady("inbox"):
                msg = self.recv("inbox")
                name = msg.node_name.strip('/')
                c = self.atompub.retrieve_collection(name) 
                if not c:
                    c = self.atompub.add_collection(name)
                    n = ItemsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost, 
                                       node_name=unicode(name))
                    self.send(n, "items-disco")

                modified = False

                for item in msg.items:
                    member_id, media_id = c.convert_id(item.id)
                    mb = c.get_member(member_id)
                    if not mb:
                        member = ResourceWrapper(c, media_type=u'application.atom+xml;type=entry')
                        try:
                            member.create_entry(source=item.payload.xml(), preserve_dates=True,
                                                slug=item.id)
                        except ResourceOperationException, ex:
                            print str(ex)
                        else:
                            member.inherit_categories_from_collection()
                            
                            c.attach(member, member_content=member.atom.xml())
                            modified = True

                if modified:
                    c.store.commit(message='Updated store')
                    # Regenerate the collection feed
                    c.feed_handler.set(c.feed)

            if not self.anyReady():
                self.pause()
  
            yield 1
