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

__all__ = ['DiscoHandler', 'ItemsHandler', 'MessageHandler']

publish_item_rx = re.compile(r'\[(.*)\] ([\w ]*)')


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
        if profile:
            self.collection = self.atompub.get_collection(profile.username)
        self.pubsub_top_level_node = u'home/%s/%s' % (self.xmpphost, self.from_jid.node)

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
                items_disco = self.recv('items.result')
                print "%s has %d item(s)" % (items_disco.node_name, len(items_disco.items))
                
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=self.pubsub_top_level_node, sub_jid=self.from_jid.nodeid())
                self.send(p, "subscribe-node")

                for item in items_disco.items:
                    p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                             node_name=self.pubsub_top_level_node, sub_jid=self.from_jid.nodeid())
                    self.send(p, "subscribe-node")
                    
                #        n = ItemsDiscovery(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost, 
                #                           node_name=item.node)
                #        self.send(n, "items-disco")
                #        yield 1

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
               "jid"        : "",}
    
    Outboxes = {"outbox"  : "",
                "publish" : "",
                "delete"  : "",
                "purge"   : "",
                "signal"  : "Shutdown signal",}

    def __init__(self, from_jid, atompub, host='localhost', session_id=None, profile=None):
        super(ItemsHandler, self).__init__() 
        self.from_jid = from_jid
        self.atompub = atompub
        self.xmpphost = host
        self.session_id = session_id
        self.collection = None
        self.profile = profile
        if profile:
            self.collection = self.atompub.get_collection(profile.username)
        self.pubsub_top_level_node = u'home/%s/%s' % (self.xmpphost, self.from_jid.node)

    def initComponents(self):
        sub = SubscribeTo("JID.%s" % self.session_id)
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        return 1

    def make_entry(self, msg):
        uuid = generate_uuid_uri()
        entry = E.load('./entry.atom').xml_root
        entry.get_child('id', ns=entry.xml_ns).xml_text =  uuid
        dt = get_isodate()
        entry.get_child('author', ns=entry.xml_ns).get_child('name', ns=entry.xml_ns).xml_text = unicode(self.profile.username)
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
                self.pubsub_top_level_node = u'home/%s/%s' % (self.xmpphost, self.from_jid.node)
            
            if self.dataReady("topublish"):
                message = self.recv("topublish")
                m = publish_item_rx.match(message)
                node = self.pubsub_top_level_node
                if m:
                    node, message = m.groups()
                print node, message
                uuid, entry = self.make_entry(message)
                i = Item(id=uuid, payload=entry)
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=node, item=i)
                self.send(p, "publish")
                yield 1

            if self.dataReady("todelete"):
                item_id = self.recv("todelete")
                i = Item(id=unicode(item_id))
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=self.pubsub_top_level_node, item=i)
                self.send(p, "delete")
                yield 1

            if self.dataReady("topurge"):
                node_id = self.recv("topurge")
                p = Node(unicode(self.from_jid), u'pubsub.%s' % self.xmpphost,
                         node_name=self.pubsub_top_level_node)
                self.send(p, "purge")
                yield 1

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
        self.collection = self.atompub.get_collection(profile.username)

    def initComponents(self):
        sub = SubscribeTo("JID.%s" % self.session_id)
        self.link((sub, 'outbox'), (self, 'jid'))
        self.addChildren(sub)
        sub.activate()

        self.client = SimpleHTTPClient()
        self.addChildren(self.client)
        self.link((self, '_request'), (self.client, 'inbox')) 
        self.link((self.client, 'outbox'), (self, '_response')) 
        self.client.activate()

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
                for item in msg.items:
                    if item.event == 'item' and item.payload:
                        member = self.collection.get_member(item.id)
                        if not member:
                            body = item.payload.xml()
                            params = {'url': self.collection.get_base_edit_uri(), 
                                      'method': 'POST', 'postbody': body,
                                      'extraheaders': {'content-type': 'application/atom+xml;type=entry',
                                                       'content-length': str(len(body)),
                                                       'slug': item.id}}
                            self.send(params, '_request') 
                    elif item.event == 'retract':
                        params = {'url': '%s/%s' % (self.collection.get_base_edit_uri().rstrip('/'),
                                                    item.id.encode('utf-8')), 
                                  'method': 'DELETE'}
                        self.send(params, '_request') 

            if not self.anyReady():
                self.pause()
  
            yield 1
