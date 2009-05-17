# -*- coding: utf-8 -*-
from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from headstock.protocol.extension.discovery import DiscoveryDispatcher, FeaturesDiscovery
from headstock.protocol.extension.pubsub import *
from headstock.api.jid import JID
from headstock.api import Entity
from headstock.api.pubsub import Node, Item, Message
from headstock.api.discovery import *
from headstock.lib.utils import generate_unique

from bridge import Element as E
from bridge.common import XMPP_CLIENT_NS, XMPP_ROSTER_NS,\
     XMPP_LAST_NS, XMPP_DISCO_INFO_NS, XMPP_DISCO_ITEMS_NS,\
     XMPP_PUBSUB_NS, XMPP_PUBSUB_OWNER_NS, XMPP_PUBSUB_EVENT_NS

__all__ = ['make_linkages', 'PubSubDiscoveryComponent', 'PubSubNodeComponent']

def make_linkages(pubsub_service):
    dcomp, dlinks = make_disco_linkages(pubsub_service)
    ncomp, nlinks = make_node_linkages(pubsub_service)

    comps = {}
    comps.update(dcomp)
    comps.update(ncomp)

    linkages = {}
    linkages.update(dlinks)
    linkages.update(nlinks)

    return comps, linkages
    
def make_disco_linkages(pubsub_service):
    linkages = {("xmpp", "%s.query" % XMPP_DISCO_INFO_NS): ("discodisp", "inbox"),
                ("xmpp", "%s.query" % XMPP_DISCO_ITEMS_NS): ("discodisp", "items.inbox"),
                ("xmpp", "%s.affiliations" % XMPP_PUBSUB_NS): ("discodisp", "affiliation.inbox"),
                ("xmpp", "%s.subscriptions" % XMPP_PUBSUB_NS): ("discodisp", "subscription.inbox"),
                ("discodisp", "log"): ('logger', "inbox"),
                ("discohandler", "features-disco"): ('discodisp', "features.forward"),
                ('discohandler', 'items-disco'): ('discodisp', 'items.forward'),
                ('discohandler', 'subscriptions-disco'): ('discodisp', 'subscription.forward'),
                ('discohandler', 'affiliations-disco'): ('discodisp', 'affiliation.forward'),
                ('discohandler', "information-disco"): ('discodisp', "info.forward"),
                ("discodisp", "out.features.result"): ('discohandler', "features.result"),
                ("discodisp",'subscription.outbox'):('xmpp','forward'),
                ("discodisp",'affiliation.outbox'):('xmpp','forward'),
                ("discodisp",'out.subscription.result'): ('discohandler','subscriptions.result'),
                ("discodisp",'out.subscription.error'): ('discohandler','subscriptions.error'),
                ("discodisp",'out.info.result'): ('discohandler','information.result'),
                ("discodisp",'out.info.error'): ('discohandler','information.error'),
                ("discodisp",'out.affiliation.result'): ('discohandler','affiliations.result'),
                ("discodisp", 'out.items.result'): ('discohandler', 'items.result'),
                ("discodisp", 'out.items.error'): ('discohandler', 'items.error'),
                ("discodisp", 'out.info.result'): ('discohandler', 'information.result'),
                ("discodisp", "outbox"): ("xmpp", "forward"),
                ('jidsplit', 'discojid'): ('discohandler', 'jid'),
                ('boundsplit', 'discobound'): ('discohandler', 'bound')}
    return dict(discohandler=PubSubDiscoveryComponent(pubsub_service),
                discodisp=DiscoveryDispatcher()), linkages

class PubSubDiscoveryComponent(component):
    Inboxes = {"inbox"       : "",
               "control"     : "", 
               "jid"         : "",
               "bound"    : "",
               
               "request-features-disco" : "",
               "request-items-disco" : "",
               "request-affiliations-disco": "",
               "request-subscriptions-disco": "",
               "request-node-subscriptions-disco": "",
               "request-information-disco": "",
               
               "subscriptions.result": "",
               "subscriptions.error": "",

               "affiliations.result": "",

               "information.result": "",
               "information.error": "",

               "features.result": "",

               "items.result": "",
               "items.error" : "",}
    
    Outboxes = {"outbox"        : "",
                "signal"        : "Shutdown signal",
                "message"       : "",
                "features-disco": "headstock.api.discovery.FeaturesDiscovery query to the server",   
                "features-announce": "headstock.api.discovery.FeaturesDiscovery informs"\
                    "the other components about the features instance received from the server",
                "items-disco"   : "",
                "information-disco": "",
                "subscriptions-disco": "",
                "affiliations-disco" : "",
                "features": "",
                "items": "",
                "info": "",
                "affiliations": "",
                "subscriptions": "",
                "items-error": "",
                "info-error": "",
                "subscriptions-error": ""}

    def __init__(self, pubsub_service):
        super(PubSubDiscoveryComponent, self).__init__()
        self.pubsub_service = pubsub_service

    def initComponents(self):
        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                       isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')
            
            if self.dataReady("bound"):
                self.recv('bound')
                
                d = FeaturesDiscovery(unicode(self.from_jid), self.pubsub_service)
                self.send(d, "features-disco")
                
                d = SubscriptionsDiscovery(unicode(self.from_jid), self.pubsub_service)
                self.send(d, "subscriptions-disco")
                
                d = AffiliationsDiscovery(unicode(self.from_jid), self.pubsub_service)
                self.send(d, "affiliations-disco")

            if self.dataReady("request-features-disco"):
                self.recv("request-features-disco")
                d = FeaturesDiscovery(unicode(self.from_jid), self.pubsub_service)
                self.send(d, "features-disco")

            if self.dataReady("request-subscriptions-disco"):
                self.recv("request-subscriptions-disco")
                d = SubscriptionsDiscovery(unicode(self.from_jid), self.pubsub_service)
                self.send(d, "subscriptions-disco")

            if self.dataReady("request-affiliations-disco"):
                self.recv("request-affiliations-disco")
                d = AffiliationsDiscovery(unicode(self.from_jid), self.pubsub_service)
                self.send(d, "affiliations-disco")

            if self.dataReady("request-node-subscriptions-disco"):
                node_name = self.recv("request-node-subscriptions-disco")
                d = SubscriptionsDiscovery(unicode(self.from_jid), self.pubsub_service, node_name=node_name)
                self.send(d, "subscriptions-disco")
                
            if self.dataReady("request-information-disco"):
                nodeid = self.recv("request-information-disco")
                d = InformationDiscovery(unicode(self.from_jid), self.pubsub_service, node_name=nodeid)
                self.send(d, "information-disco")

            if self.dataReady("request-items-disco"):
                node_name = self.recv("request-items-disco")
                n = ItemsDiscovery(unicode(self.from_jid), self.pubsub_service, node_name=node_name)
                self.send(n, "items-disco")

            if self.dataReady('items.error'):
                items = self.recv('items.error')
                self.send(items, 'items-error')
                
            if self.dataReady('subscriptions.error'):
                subscriptions = self.recv('subscriptions.error')
                self.send(subscriptions, 'subscriptions-error')
                
            if self.dataReady('information.error'):
                info = self.recv('information.error')
                self.send(info, 'info-error')
                
            if self.dataReady('features.result'):
                disco = self.recv('features.result')
                self.send(disco, 'features')
                
            if self.dataReady('items.result'):
                items = self.recv('items.result')
                self.send(items, 'items')
                
            if self.dataReady('information.result'):
                info = self.recv('information.result')
                self.send(info, 'info')
                
            if self.dataReady('subscriptions.result'):
                subscriptions = self.recv('subscriptions.result')
                self.send(subscriptions, 'subscriptions')

            if self.dataReady('affiliations.result'):
                affiliations = self.recv('affiliations.result')
                self.send(affiliations, 'affiliations')

            if not self.anyReady():
                self.pause()
  
            yield 1

def make_node_linkages(pubsub_service):
    linkages = {("xmpp", "%s.create" % XMPP_PUBSUB_NS): ("pubsubdisp", "create.inbox"),
                ("xmpp", "%s.delete" % XMPP_PUBSUB_OWNER_NS): ("pubsubdisp", "delete.inbox"),
                ("xmpp", "%s.purge" % XMPP_PUBSUB_NS): ("pubsubdisp", "purge.inbox"),
                ("xmpp", "%s.subscribe" % XMPP_PUBSUB_NS): ("pubsubdisp", "subscribe.inbox"),
                ("xmpp", "%s.unsubscribe" % XMPP_PUBSUB_NS):("pubsubdisp", "unsubscribe.inbox"),
                ("xmpp", "%s.publish" % XMPP_PUBSUB_NS): ("pubsubdisp", "publish.inbox"),
                ("xmpp", "%s.retract" % XMPP_PUBSUB_NS): ("pubsubdisp", "retract.inbox"),
                ("xmpp", "%s.items" % XMPP_PUBSUB_NS): ("pubsubdisp", "retrieve.inbox"),
                ("xmpp", "%s.x" % XMPP_PUBSUB_EVENT_NS): ("pubsubdisp", "message.inbox"),
                ("xmpp", "%s.event" % XMPP_PUBSUB_EVENT_NS): ("pubsubdisp", "message.inbox"),
                ("pubsubdisp", "log"): ('logger', "inbox"),
                ("itemshandler", "create-node"): ("pubsubdisp", "create.forward"),
                ("itemshandler", "delete-node"): ("pubsubdisp", "delete.forward"),
                ("itemshandler", "retrieve-item"): ("pubsubdisp", "retrieve.forward"),
                ("itemshandler", "retrieve-all-items"): ("pubsubdisp", "retrieve.all.forward"),
                ("itemshandler", "subscribe-node"): ("pubsubdisp", "subscribe.forward"),
                ("itemshandler", "unsubscribe-node"): ("pubsubdisp", "unsubscribe.forward"),
                ('itemshandler', 'publish-item'): ('pubsubdisp', 'publish.forward'),
                ('itemshandler', 'delete-item'): ('pubsubdisp', 'retract.forward'),
                ('itemshandler', 'purge-collection-node'): ('pubsubdisp', 'purge.forward'),
                ("pubsubdisp", "retrieve.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "retrieve.all.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "create.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "delete.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "purge.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "subscribe.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "unsubscribe.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "publish.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "retract.outbox"): ("xmpp", "forward"),
                ("pubsubdisp", "out.message"): ('itemshandler', 'message.received'),
                ("pubsubdisp", "out.message.purge"): ('itemshandler', 'purged'),
                ("pubsubdisp", "out.retrieve.result"): ("itemshandler", "retrieved"),
                ("pubsubdisp", "out.retrieve.all.result"): ("itemshandler", "retrieved"),
                ("pubsubdisp", "out.create.result"): ("itemshandler", "created"),
                ("pubsubdisp", "out.subscribe.result"): ("itemshandler", "subscribed"),
                ("pubsubdisp", "out.delete.result"): ("itemshandler", "deleted"),
                ("pubsubdisp", "out.retrieve.error"): ("itemshandler", "error"),
                ("pubsubdisp", "out.retrieve.all.error"): ("itemshandler", "error"),
                ("pubsubdisp", "out.create.error"): ("itemshandler", "error"),
                ("pubsubdisp", "out.delete.error"): ("itemshandler", "error"),
                ("pubsubdisp", "out.purge.error"): ("itemshandler", "error"),
                ("pubsubdisp", "out.publish.error"): ("itemshandler", "publish.error"),
                ("pubsubdisp", "out.retract.error"): ("itemshandler", "retract.error"),
                ("pubsubdisp", "out.publish.result"): ("itemshandler", "published"),
                ('jidsplit', 'pubsubnodejid'): ('itemshandler', 'jid'),
                ('boundsplit', 'pubsubnodebound'): ('itemshandler', 'bound')}
    return dict(itemshandler=PubSubNodeComponent(pubsub_service),
                pubsubdisp=PubSubDispatcher()), linkages
        
class PubSubNodeComponent(component):
    Inboxes = {"inbox"       : "",
               "control"     : "", 
               "jid"         : "",
               "bound"    : "",
               
               "request-create-node" : "",
               "request-create-collection-node": "",
               "request-delete-node" : "",
               "request-unsubscribe-node" : "",
               "request-subscribe-node" : "",
               "request-publish-item":     "",
               "request-delete-item":     "",
               "request-item": "",
               "request-all-items": "",
               "request-purge-collection-node": "",
               
               "subscribed": "",
               "retrieved": "",
               "created": "",
               "deleted" : "",
               "purged" : "",
               "error"       : "",
               "message.received": "",
               "xmpp.result": "",
               "published": "",
               "publish.error": "",
               "retract.error": ""}
    
    Outboxes = {"outbox"        : "",
                "signal"        : "Shutdown signal",
                "create-node"   : "",
                "delete-node"   : "",
                "publish-item"  : "",
                "delete-item"  : "",
                "retrieve-item": "",
                "retrieve-all-items": "",
                "purge-collection-node": "",
                "subscribe-node"   : "",
                "unsubscribe-node"   : "",
                "node-error": "",
                "retrieved-node": "",
                "created-node": "",
                "subscribed-node": "",
                "deleted-node": "",
                "received-message": "",
                "purged-node": ""}

    def __init__(self, pubsub_service):
        super(PubSubNodeComponent, self).__init__()
        self.pubsub_service = pubsub_service

    def initComponents(self):
        return 1

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                       isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("jid"):
                self.from_jid = self.recv('jid')

            if self.dataReady("bound"):
                self.recv('bound')

            if self.dataReady('error'):
                node = self.recv('error')
                self.send(node, 'node-error')

            if self.dataReady('request-create-node'):
                nodeid = self.recv('request-create-node')

                p = Node(unicode(self.from_jid), self.pubsub_service, node_name=nodeid)
                self.send(p, "create-node")

            if self.dataReady('request-item'):
                node_id, item_id = self.recv('request-item')
                p = Node(unicode(self.from_jid), self.pubsub_service, type=u"get",
                         node_name=node_id, item=Item(id=item_id))
                self.send(p, "retrieve-item")

            if self.dataReady('request-all-items'):
                node_id = self.recv('request-all-items')
                p = Node(unicode(self.from_jid), self.pubsub_service, type=u"get",
                         node_name=node_id)
                self.send(p, "retrieve-all-items")

            if self.dataReady('request-publish-item'):
                node_id, item_id, data = self.recv('request-publish-item')
                i = Item(id=item_id, payload=data)
                p = Node(unicode(self.from_jid), self.pubsub_service, 
                         node_name=node_id, item=i)
                self.send(p, "publish-item")

            if self.dataReady('request-delete-item'):
                node_id, item_id = self.recv('request-delete-item')
                i = Item(id=item_id)
                p = Node(unicode(self.from_jid), self.pubsub_service, 
                         node_name=node_id, item=i)
                self.send(p, "delete-item")

            if self.dataReady('request-create-collection-node'):
                nodeid = self.recv('request-create-collection-node').strip()

                p = Node(unicode(self.from_jid), self.pubsub_service, node_name=nodeid)
                p.set_default_collection_conf()
                self.send(p, "create-node")

            if self.dataReady('request-delete-node'):
                nodeid = self.recv('request-delete-node')
                p = Node(unicode(self.from_jid), self.pubsub_service, node_name=nodeid)
                self.send(p, "delete-node")

            if self.dataReady('request-purge-collection-node'):
                nodeid = self.recv('request-purge-collection-node')
                p = Node(unicode(self.from_jid), self.pubsub_service, node_name=nodeid)
                self.send(p, "purge-collection-node")

            if self.dataReady('request-subscribe-node'):
                nodeid = self.recv('request-subscribe-node')
                p = Node(unicode(self.from_jid), self.pubsub_service,
                         node_name=nodeid, sub_jid=self.from_jid.nodeid())
                self.send(p, "subscribe-node")

            if self.dataReady('request-unsubscribe-node'):
                nodeid = self.recv('request-unsubscribe-node')
                p = Node(unicode(self.from_jid), self.pubsub_service,
                         node_name=nodeid, sub_jid=self.from_jid.nodeid())
                self.send(p, "unsubscribe-node")
            
            if self.dataReady('retrieved'):
                node = self.recv('retrieved')
                self.send(node, "retrieved-node")
                
            if self.dataReady('created'):
                node = self.recv('created')
                self.send(node, "created-node")
                
            if self.dataReady('subscribed'):
                node = self.recv('subscribed')
                self.send(node, "subscribed-node")

            if self.dataReady('deleted'):
                node = self.recv('deleted')
                self.send(node, "deleted-node")
                
            if self.dataReady("message.received"):
                message = self.recv("message.received")
                self.send(node, "received-message")
                
            if self.dataReady('purged'):
                message = self.recv('purged')
                self.send(node, "purged-node")
                
            if not self.anyReady():
                self.pause()
  
            yield 1
