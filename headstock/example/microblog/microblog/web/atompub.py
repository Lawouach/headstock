# -*- coding: utf-8 -*-
import os
import cherrypy

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

import microblog.web.ampleetool
from microblog.profile.manager import ProfileManager
from microblog.atompub.resource import ResourceWrapper

__all__ = ['AtomPubWebApplication', 'CollectionHandler',
           'CollectionPagingHandler', 'CollectionTagingHandler']

class AtomPubWebApplication(object):
    def __init__(self, base_dir, atompub, tpl_lookup):
        self.base_dir = base_dir
        self.atompub = atompub
        self.tpl_lookup = tpl_lookup
        
    def service_head(self, *args, **kwargs):
        content = self.GET(*args, **kwargs)
        cherrypy.response.headers['Content-Length'] = len(content)

    def service_get(self):
        cherrypy.response.headers['Content-Type'] = 'application/atomsvc+xml'
        return self.atompub.service.to_service().xml(indent=True)

class CollectionHandler(object):
    _cp_config = {'tools.amplee_request_body.on': True,
                  'tools.openid.on': False}
    
    def __init__(self, collection):
        self.collection = collection
        self.most_recent_member = None

    ##########################################
    # Helpers
    ##########################################
    def __check_content_type(self):
        ct = cherrypy.request.headers.get('Content-Type')
        if not ct:
            raise cherrypy.HTTPError(400, "Missing content type")

        mimetype = get_best_mimetype(ct, self.collection.editable_media_types,
                                     check_params=False, return_full=True)
        if not mimetype:
            raise cherrypy.HTTPError(415, 'Unsupported Media Type')

        # The problem with this media-type is that it also contains
        # the multipart boundary value within the media-type
        # and that value is per client so here we do force
        # the media-type to be stripped of its parameters
        if mimetype.startswith('multipart/form-data'):
            mimetype = 'multipart/form-data'

        return mimetype

    def __check_length(self):
        length = cherrypy.request.headers.get('Content-Length')
        if not length:
            raise cherrypy.HTTPError(411, 'Length Required')
        return int(length)

    def __get_member(self, id):
        id = safe_unquote(id)
        member_id, media_id = self.collection.convert_id(id)
        member = self.collection.get_member(member_id)
        if not member:
            raise cherrypy.NotFound()
        return member
        
    ##########################################
    # Web Service interface
    ##########################################
    def feed(self):
        collection_feed = self.collection.feed_handler.retrieve()
        cherrypy.response.headers['etag'] = compute_etag_from_feed(collection_feed)
        cherrypy.response.headers['content-type'] = 'application/atom+xml;type=feed'
        return self.collection.feed_handler.collection_xml()

    def retrieve(self, id):
        member = self.__get_member(id)

        if id.endswith('.atom'):
            content = member.xml(indent=True)
            cherrypy.response.headers['Content-Type'] = 'application/atom+xml;type=entry'
        else:
            content = member.content
            member.media_type = extract_media_type(member.atom)
            cherrypy.response.headers['Content-Type'] = member.media_type
            
        cherrypy.response.headers['ETag'] = compute_etag_from_entry(member.atom)

        return content
    
    def retrieve_head(self, id):
        content = self.retrieve(id)
        cherrypy.response.headers['Content-Length'] = len(content)

    def create(self):
        mimetype = self.__check_content_type()
        length = self.__check_length()
        slug = decode_slug(cherrypy.request.headers.get('slug', None))
        
        member = ResourceWrapper(self.collection, media_type=mimetype)
        content = member.generate(mimetype, source=cherrypy.request.body, slug=slug,
                                  length=length, preserve_dates=True)
        member.inherit_categories_from_collection()
        
        media_content = None
        if not member.is_entry_mimetype(mimetype):
            media_content = content.read(length)

        # Here there is a subtle difference between the dejavu storage
        # and other kind of storages.
        # When using dejavu, you have to commit the atom and media content
        # in two steps so that the table integrity is kept
        # If you are not using dejavu as a storage you can 
        # collapse the .attach(...) call into one single call that
        # will store data at once. In fact if you do use dejavu but
        # with two distinct databases you can also collapse both 
        # calls into a single one.
        self.collection.attach(member, member_content=member.atom.xml())
        self.collection.store.commit(message='Adding %s' % member.member_id)

        self.collection.attach(member, media_content=media_content)
        self.collection.store.commit(message='Adding %s' % member.media_id)

        # Regenerate the collection feed
        self.collection.feed_handler.set(self.collection.feed)

        cherrypy.response.status = '201 Created'
        member_uri = member.member_uri
        if member_uri:
            member_uri = member_uri.encode('utf-8')
            cherrypy.response.headers['Location'] = member_uri
            cherrypy.response.headers['Content-Location'] = member_uri
            
        cherrypy.response.headers['Content-Type'] = u'application/atom+xml;type=entry'
        cherrypy.response.headers['ETag'] = compute_etag_from_entry(member.atom)

        self.most_recent_member = member

        return member.xml(indent=True)
        
    def replace(self, id):
        mimetype = self.__check_content_type()
        length = self.__check_length()
        member = self.__get_member(id)

        if cherrypy.request.headers.get('If-Match'):
            try:
                handle_if_match(compute_etag_from_entry(member.atom),
                                cherrypy.request.headers.elements('If-Match') or [])
                # We want to prevent the CherryPy Etag tool to process this header
                # again and break the response
                del cherrypy.request.headers['If-Match']
            except ResourceOperationException, roe:
                raise cherrypy.HTTPError(roe.code, roe.msg)

        new_member = ResourceWrapper(self.collection, media_type=mimetype)
        content = new_member.generate(mimetype, source=cherrypy.request.body,
                                      existing_member=member, length=length)
        new_member.use_published_date_from(member) # let's keep the published date
        new_member.update_dates() # but update the other dates
        
        media_content = None
        if not new_member.is_entry_mimetype(mimetype):
            media_content = content.read(length)

        self.collection.attach(new_member, member_content=new_member.atom.xml(),
                               media_content=media_content)
        self.collection.store.commit(message='Updating %s' % new_member.member_id)

        # Regenerate the collection feed
        self.collection.feed_handler.set(self.collection.feed)
        
        cherrypy.response.headers['Content-Type'] = mimetype
        cherrypy.response.headers['ETag'] = compute_etag_from_entry(new_member.atom)
        return new_member.xml()

    def remove(self, id):
        id = safe_unquote(id)
        member_id, media_id = self.collection.convert_id(id)
        member = self.collection.get_member(member_id)
        if member:
            self.collection.prune(member.member_id, member.media_id)
            self.collection.store.commit(message="Deleting %s and %s" % (member.member_id,
                                                                         member.media_id))
            
            # Regenerate the collection feed
            self.collection.feed_handler.set(self.collection.feed)

class CollectionPagingHandler(object):
    def __init__(self, collection):
        self.collection = collection

    def GET(self, start):
        if not start: start = 0
        start = int(start)
        
        members = self.collection.reload_members(start=start, limit=10)
        feed = self.collection.to_feed(members=members)

        attrs = {u'rel': u'first', u'type': u'application/atom+xml;type=feed',
                 u'href': safe_url_join([self.collection.get_base_edit_uri(), u'paging'])}
        feed.feed.xml_append(feed.xml_create_element(qname(u"link", feed.feed.prefix),
                                                     ns=feed.feed.namespaceURI,
                                                     attributes=attrs))

        if start > 10:
            attrs = {u'rel': u'previous', u'type': u'application/atom+xml;type=feed',
                     u'href': safe_url_join([self.collection.get_base_edit_uri(),
                                             u'paging?start=%s' % unicode(start-10)])}
            feed.feed.xml_append(feed.xml_create_element(qname(u"link", feed.feed.prefix),
                                                         ns=feed.feed.namespaceURI,
                                                         attributes=attrs))
            
        attrs = {u'rel': u'next', u'type': u'application/atom+xml;type=feed',
                 u'href': safe_url_join([self.collection.get_base_edit_uri(),
                                         u'paging?start=%s' % unicode(start+10)])}
        feed.feed.xml_append(feed.xml_create_element(qname(u"link", feed.feed.prefix),
                                                     ns=feed.feed.namespaceURI,
                                                     attributes=attrs))
        
        cherrypy.response.headers['etag'] = compute_etag_from_feed(feed)
        cherrypy.response.headers['content-type'] = 'application/atom+xml;type=feed'
        return feed.xml(indent=True)

class CollectionTagingHandler(object):
    def __init__(self, collection):
        self.collection = collection
        self.cat_index = self.collection.indexers[0].retrieve('ci')

    def index(self, tag):
        res = self.cat_index.lookup(term=tag)
        if res:
            member_ids = [member_id for collection, member_id in res]
            members = self.collection.reload_members_from_list(member_ids)
            feed = self.collection.to_feed(members=members)
            cherrypy.response.headers['etag'] = compute_etag_from_feed(feed)
            cherrypy.response.headers['content-type'] = 'application/atom+xml;type=feed'
            return feed.xml(indent=True)

        return "No results"
