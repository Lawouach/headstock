# -*- coding: utf-8 -*-
import re

from Axon.Component import component
from Kamaelia.Util.Backplane import PublishTo, SubscribeTo
from Axon.Ipc import shutdownMicroprocess, producerFinished
from Kamaelia.Protocol.HTTP.HTTPClient import SimpleHTTPClient
    
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

from microblog.atompub.resource import ResourceWrapper
from microblog.jabber.atomhandler import FeedReaderComponent

__all__ = ['DiscoHandler', 'ItemsHandler', 'MessageHandler']

publish_item_rx = re.compile(r'\[(.*)\] ([\w ]*)')
retract_item_rx = re.compile(r'\[(.*)\] ([\w:\-]*)')


class DiscoHandler(component):
    Inboxes = {"inbox"       : "",
               "control"     : "", 
               "initiate"    : "",
               "jid"         : "",
               "error"       : "",
               "features.result": "",
               "items.result": "",
               "items.error" : "",
               "docreate" : "",
               "docreatecollection": "",
               "dodelete" : "",
               "dounsubscribe" : "",
               "dosubscribe" : "",
               "subscribed": "",
               "subscriptions.result": "",
               "affiliations.result": "",
               "created": "",
               "deleted" : ""}
    
    Outboxes = {"outbox"        : "",
                "signal"        : "Shutdown signal",
                "message"       : "",
                "features-disco": "headstock.api.discovery.FeaturesDiscovery query to the server",   
                "features-announce": "headstock.api.discovery.FeaturesDiscovery informs"\
                    "the other components about the features instance received from the server",
                "items-disco"   : "",
                "create-node"   : "",
                "delete-node"   : "",
                "subscribe-node"   : "",
                "unsubscribe-node"   : "",
                "subscriptions-disco": "",
                "affiliations-disco" : ""}

    def __init__(self, from_jid, atompub, host='localhost', session_id=None, profile=None):
        super(DiscoHandler, self).__init__() 
        self.from_jid = from_jid
        self.atompub = atompub
        self.xmpphost = host
        self.session_id = session_id
        self.profile = profile
        self._collection = None
        self.pubsub_top_level_node = u'home/%s/%s' % (self.xmpphost, self.from_jid.node)

    @property
    def collection(self):
        # Lazy loading of collection
        if not self._collection:
            self._collection = self.atompub.get_collection(self.profile.username)
        return self._collection

    def initComponents(self):
        sub = SubscribeTo("JID.%s" % self.session_id)
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        pub = PublishTo("DISCO_FEAT.%s" % self.session_id)
        self.link((self, 'features-announce'), (pub, 'inbox'))
        self.addChildren(pub)
        pub.activate()

        sub = SubscribeTo("BOUND.%s" % self.session_id)
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
                self.pubsub_top_level_node = u'home/%s/%s' % (self.xmpphost, self.from_jid.node)
            
            if self.dataReady("initiate"):
                self.recv("initiate")
                
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=self.pubsub_top_level_node)
                self.send(p, "create-node")
                yield 1                    

                #d = FeaturesDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost)
                #self.send(d, "features-disco")

                d = SubscriptionsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost)
                self.send(d, "subscriptions-disco")
                
                d = AffiliationsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost)
                self.send(d, "affiliations-disco")

                n = ItemsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost, 
                                   node_name=self.pubsub_top_level_node)
                self.send(n, "items-disco")

            # The response to our discovery query
            # is a a headstock.api.discovery.FeaturesDiscovery instance.
            # What we immediatly do is to notify all handlers
            # interested in that event about it.
            if self.dataReady('features.result'):
                disco = self.recv('features.result')
                for feature in disco.features:
                    print "  ", feature.var
                self.send(disco, 'features-announce')

            if self.dataReady('items.result'):
                items = self.recv('items.result')
                print "%s has %d item(s)" % (items.node_name, len(items.items))

                #for item in items.items:
                    #n = ItemsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost, 
                    #                   node_name=item.node)
                    #self.send(n, "items-disco")

            if self.dataReady('items.error'):
                items_disco = self.recv('items.error')
                print "DISCO ERROR: ", items_disco.node_name, items_disco.error

                if items_disco.error.condition == 'item-not-found':
                    p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                             node_name=items_disco.node_name)
                    self.send(p, "create-node")
                    yield 1                    
                
            if self.dataReady('subscriptions.result'):
                subscriptions = self.recv('subscriptions.result')
                for sub in subscriptions.subscriptions:
                    print "Subscription: %s (%s)" % (sub.node, sub.state)

            if self.dataReady('affiliations.result'):
                affiliations = self.recv('affiliations.result')
                for aff in affiliations.affiliations:
                    print "Affiliation: %s %s" % (aff.node, aff.affiliation)

            if self.dataReady('docreate'):
                nodeid = self.recv('docreate').strip()

                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=nodeid)
                self.send(p, "create-node")

            if self.dataReady('docreatecollection'):
                nodeid = self.recv('docreatecollection').strip()

                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=nodeid)
                p.set_default_collection_conf()
                self.send(p, "create-node")

            if self.dataReady('dodelete'):
                nodeid = self.recv('dodelete').strip()
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=nodeid)
                self.send(p, "delete-node")

            if self.dataReady('dosubscribe'):
                nodeid = self.recv('dosubscribe').strip()
                
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=nodeid, sub_jid=self.from_jid.nodeid())
                self.send(p, "subscribe-node")

            if self.dataReady('dounsubscribe'):
                nodeid = self.recv('dounsubscribe').strip()
                
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=nodeid, sub_jid=self.from_jid.nodeid())
                self.send(p, "unsubscribe-node")
            
            if self.dataReady('created'):
                node = self.recv('created')
                print "Node created: %s" % node.node_name
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=node.node_name, sub_jid=self.from_jid.nodeid())
                self.send(p, "subscribe-node")
                
            if self.dataReady('subscribed'):
                node = self.recv('subscribed')
                print "Node subscribed: %s" % node.node_name

            if self.dataReady('deleted'):
                node = self.recv('deleted')
                print "Node deleted: %s" % node.node_name
                
            if self.dataReady('error'):
                node = self.recv('error')
                print node.error
                
            if not self.anyReady():
                self.pause()
  
            yield 1

class ItemsHandler(component):
    Inboxes = {"inbox"      : "",
               "topublish"    : "",
               "todelete" : "",
               "topurge": "",
               "control"    : "", 
               "xmpp.result": "",
               "published": "",
               "publish.error": "",
               "retract.error": "",
               "jid"        : "",
               "_feedresponse": "",
               "_delresponse": ""}
    
    Outboxes = {"outbox"  : "",
                "publish" : "",
                "delete"  : "",
                "purge"   : "",
                "signal"  : "Shutdown signal",
                "_feedrequest": "",
                "_delrequest": ""}

    def __init__(self, from_jid, atompub, host='localhost', session_id=None, profile=None):
        super(ItemsHandler, self).__init__() 
        self.from_jid = from_jid
        self.atompub = atompub
        self.xmpphost = host
        self.session_id = session_id
        self.profile = profile
        self._collection = None
        self.pubsub_top_level_node = u'home/%s/%s' % (self.xmpphost, self.from_jid.node)

    @property
    def collection(self):
        # Lazy loading of collection
        if not self._collection:
            self._collection = self.atompub.get_collection(self.profile.username)
        return self._collection

    def initComponents(self):
        sub = SubscribeTo("JID.%s" % self.session_id)
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        feedreader = FeedReaderComponent(use_etags=False)
        self.addChildren(feedreader)
        feedreader.activate()
        
        client = SimpleHTTPClient()
        self.addChildren(client)
        self.link((self, '_feedrequest'), (client, 'inbox')) 
        self.link((client, 'outbox'), (feedreader, 'inbox'))
        self.link((feedreader, 'outbox'), (self, '_feedresponse'))
        client.activate()

        client = SimpleHTTPClient()
        self.addChildren(client)
        self.link((self, '_delrequest'), (client, 'inbox')) 
        self.link((client, 'outbox'), (self, '_delresponse'))
        client.activate()

        return 1

    def make_entry(self, msg, node):
        uuid = generate_uuid_uri()
        entry = E.load('./entry.atom').xml_root
        entry.get_child('id', ns=entry.xml_ns).xml_text =  uuid
        dt = get_isodate()
        entry.get_child('author', ns=entry.xml_ns).get_child('name', ns=entry.xml_ns).xml_text = unicode(self.profile.username)
        entry.get_child('published', ns=entry.xml_ns).xml_text = dt
        entry.get_child('updated', ns=entry.xml_ns).xml_text = dt
        entry.get_child('content', ns=entry.xml_ns).xml_text = unicode(msg)

        if node != self.pubsub_top_level_node:
            tag = extract_url_trail(node)
            E(u'category', namespace=entry.xml_ns, prefix=entry.xml_prefix,
              attributes={u'term': unicode(tag)}, parent=entry)
        
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
                self.pubsub_top_level_node = u'home/%s/%s' % (self.xmpphost, self.from_jid.node)
            
            if self.dataReady("topublish"):
                message = self.recv("topublish")
                m = publish_item_rx.match(message)
                node = self.pubsub_top_level_node
                if m:
                    node, message = m.groups()
                uuid, entry = self.make_entry(message, node)
                i = Item(id=uuid, payload=entry)
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=unicode(node), item=i)
                self.send(p, "publish")
                yield 1

            if self.dataReady("todelete"):
                item_id = self.recv("todelete")
                node = self.pubsub_top_level_node
                m = retract_item_rx.match(item_id)
                if m:
                    node, item_id = m.groups()
                i = Item(id=unicode(item_id))
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=unicode(node), item=i)
                self.send(p, "delete")
                yield 1

            if self.dataReady("topurge"):
                node_id = self.recv("topurge")
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=node_id)
                self.send(p, "purge")

                params = {'url': '%s/feed' % (self.collection.get_base_edit_uri().rstrip('/')), 
                          'method': 'GET'}
                self.send(params, '_feedrequest') 

            if self.dataReady("published"):
                node = self.recv("published")
                print "Item published: %s" % node

            if self.dataReady("publish.error"):
                node = self.recv("publish.error")
                print node.error

            if self.dataReady("retract.error"):
                node = self.recv("retract.error")
                print node.error

            if self.dataReady("_feedresponse"):
                feed = self.recv("_feedresponse")
                for entry in feed.entries:
                    for link in entry.links:
                        if link.rel == 'edit':
                            params = {'url': link.href, 'method': 'DELETE'}
                            self.send(params, '_delrequest') 

            if self.dataReady("_delresponse"):
                self.recv("_delresponse")

            if not self.anyReady():
                self.pause()
  
            yield 1

class MessageHandler(component):
    Inboxes = {"inbox"      : "",
               "control"    : "",
               "jid"        : "",
               "_response"  : ""}
    
    Outboxes = {"outbox"  : "",
                "signal"  : "Shutdown signal",
                "items-disco"   : "",
                "_request": ""}

    def __init__(self, from_jid, atompub, host='localhost', session_id=None, profile=None):
        super(MessageHandler, self).__init__() 
        self.from_jid = from_jid
        self.atompub = atompub
        self.xmpphost = host
        self.session_id = session_id
        self.profile = profile
        self._collection = None
        
    @property
    def collection(self):
        # Lazy loading of collection
        if not self._collection:
            self._collection = self.atompub.get_collection(self.profile.username)
        return self._collection

    def initComponents(self):
        sub = SubscribeTo("JID.%s" % self.session_id)
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        client = SimpleHTTPClient()
        self.addChildren(client)
        self.link((self, '_request'), (client, 'inbox')) 
        self.link((client, 'outbox'), (self, '_response')) 
        client.activate()

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
            
            if self.dataReady("_response"):
                #discard the HTTP response for now
                member_entry = self.recv("_response")
                
            if self.dataReady("inbox"):
                msg = self.recv("inbox")
                collection = self.collection
                if collection:
                    for item in msg.items:
                        if item.event == 'item' and item.payload:
                            print "Published item: %s" % item.id
                            member = collection.get_member(item.id)
                            if not member:
                                if isinstance(item.payload, list):
                                    body = item.payload[0].xml()
                                else:
                                    body = item.payload.xml()
                                params = {'url': collection.get_base_edit_uri(), 
                                          'method': 'POST', 'postbody': body,
                                          'extraheaders': {'content-type': 'application/atom+xml;type=entry',
                                                           'content-length': str(len(body)),
                                                           'slug': item.id}}
                                self.send(params, '_request') 
                        elif item.event == 'retract':
                            print "Removed item: %s" % item.id
                            params = {'url': '%s/%s' % (collection.get_base_edit_uri().rstrip('/'),
                                                        item.id.encode('utf-8')), 
                                      'method': 'DELETE'}
                            self.send(params, '_request') 

            if not self.anyReady():
                self.pause()
  
            yield 1
