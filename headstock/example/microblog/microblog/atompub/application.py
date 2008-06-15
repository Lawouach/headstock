# -*- coding: utf-8 -*-
import os, os.path

from amplee.indexer import *
from amplee.atompub.collection import FeedHandler
from amplee.loader import AtomPubLoader
from amplee.error import ResourceOperationException
from amplee.utils.mediatype import get_best_mimetype
from amplee.atompub.workspace import *
from amplee.atompub.collection import *
from amplee.utils import get_isodate, generate_uuid_uri, \
     compute_etag_from_feed, compute_etag_from_entry, \
     decode_slug, handle_if_match, safe_unquote, \
     extract_media_type, extract_url_trail, \
     safe_url_join, extract_url_path_info, qname
from amplee.error import UnknownResource

from bridge import Element as E

from microblog.atompub.resource import ResourceWrapper, \
    ProfileResource

__all__ = ['AtomPubApplication']

class AtomPubApplication(object):
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.setup_index()
        self.setup_atompub()
    
    def setup_index(self):
        index = Indexer()
        container = ShelveContainer(os.path.join(self.base_dir, 'index.p'))
        index.register(PublishedIndex('pi', container=container, granularity=DateIndex.day))
        index.register(UpdatedIndex('ui', container=container, granularity=DateIndex.minute))
        index.register(EditedIndex('ei', container=container, granularity=DateIndex.minute))
        index.register(AuthorIndex('ai', container=container, index_email=True, index_uri=True))
        index.register(CategoryIndex('ci', container=container))
        
        self.indexer = index
    
    def setup_atompub(self): 
        apl = AtomPubLoader(self.base_dir)
        self.service, self.xmldoc = apl.load(os.path.join(self.base_dir, 'config.xml'),
                                             os.path.join(self.base_dir, 'service.xml'))

        self.complete_service_loading()

    def complete_service_loading(self):
        # When a service is loaded from a service document
        # some information must be set manually after the loading process
        # as they couldn't be guessed by amplee

        for workspace in self.service.workspaces:
            workspace.name_or_id = workspace.xml_attrs.get('id', None)

        for collection in self.service.get_collections():
            self.setup_collection(collection)

    def setup_collection(self, collection):
        # Because the service loader doesn't have the notiuon
        # of an id for the collection, we first need to
        # create one. For this example, we use the path info
        # at which the collection can be located
        pi = extract_url_path_info(collection.get_base_edit_uri()).strip('/')
        collection.name_or_id = u'collection-%s' % pi.replace('/', '-')
        collection.workspace.name_or_id = u'workspace-%s' % pi.replace('/', '-')

        # Next we use that id to ensure the repository structure
        # is correctly created
        collection.store.storage.create_container(pi)
        collection.store.media_storage.create_container(pi)

        # Set the index
        collection.add_indexer(self.indexer)

        # We indicate what class needs to be used when loading members
        workspace = collection.workspace
        if workspace.xml_attrs and workspace.xml_attrs.get('id') == 'workspace-profile':
            collection.set_member_class(ProfileResource)
        else:
            collection.set_member_class(ResourceWrapper)

        # Reload members so that the index is updated (in case you'd delete it ;))
        collection.reload_members()

        # We instantiate the feed handler
        collection.feed_handler = FeedHandler()
        # Resest the collection feed cache 
        collection.feed_handler.set(collection.feed)

        # We look for a link that would indicate the public URI of this collection
        query = '//app:collection[@href="%s"]/atom:link[@type="application/atom+xml;type=feed"]'

        # Make sure you use the base_edit_uri so that you get the exact value of
        # the href attribute, if you use the get_base_edit_uri() method you get
        # the extended value prefixed with any potential xml:base found in one
        # of the ancestor of the app:collection element
        query = query % collection.base_edit_uri

        result = self.xmldoc.xml_xpath(query)
        if result:
            link = result.pop()
            collection.base_uri = unicode(link.href)

    def add_workspace(self, profile_name):
        id = u'workspace-%s' % profile_name.replace('/', '-')
        return AtomPubWorkspace(self.service, id, 
                                title=unicode(profile_name), xml_attrs={u'id': id})
        
    def add_collection(self, workspace, profile_name):
        info = self.service.store.storage.info(profile_name)
        self.service.store.storage.create_container(info.key)

        id = u'collection-%s' % profile_name.replace('/', '-')
        c = AtomPubCollection(workspace, name_or_id=id, title=unicode(profile_name), xml_attrs={u'id': id},
                              base_uri=unicode(profile_name), base_edit_uri=unicode(profile_name),
                              accept_media_types=u'application/atom+xml;type=entry')
        self.setup_collection(c)
        return c

    def save_service(self):
        # Let's save this to the service document
        xml = self.service.to_service(include_workspace_id=True).xml(indent=True)
        file(os.path.join(self.base_dir, 'service.xml'), 'wb').write(xml)

    def get_collection(self, profile_name):
        id = u'collection-%s' % profile_name.replace('/', '-')
        return self.service.get_collection(id)

    def create_entry(self, text):
        uuid = generate_uuid_uri()
        entry = E.load('./entry.atom').xml_root
        entry.get_child('id', ns=entry.xml_ns).xml_text =  uuid
        dt = get_isodate()
        entry.get_child('published', ns=entry.xml_ns).xml_text = dt
        entry.get_child('updated', ns=entry.xml_ns).xml_text = dt
        entry.get_child('content', ns=entry.xml_ns).xml_text = unicode(text)
        return uuid, entry
