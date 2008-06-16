# -*- coding: utf-8 -*-
import os.path

import cherrypy

from amplee.atompub.collection import FeedHandler
from amplee.error import ResourceOperationException
from amplee.utils import get_isodate, generate_uuid_uri, \
     compute_etag_from_feed, compute_etag_from_entry, \
     decode_slug, handle_if_match, safe_unquote, \
     extract_media_type, extract_url_trail, \
     safe_url_join, extract_url_path_info, qname

from microblog.web import MICROBLOG_SESSION_PROFILE
from microblog.web.oidtool import DEFAULT_SESSION_NAME
from microblog.profile.manager import ProfileManager
from microblog.profile.user import UserProfile, EmptyUserProfile
from microblog.atompub.resource import ProfileResource

__all__ = ['UserProfileAtomPubWebApplication']

class UserProfileAtomPubWebApplication(object):
    _cp_config = {'tools.user_profile_parser.on': True}

    def __init__(self, base_dir, atompub, collection, tpl_lookup):
        self.base_dir = base_dir
        self.atompub = atompub
        self.collection = collection
        self.tpl_lookup = tpl_lookup

    ##########################################
    # Helpers
    ##########################################
    def __check_content_type(self):
        ct = cherrypy.request.headers.get('Content-Type')
        if not ct:
            raise cherrypy.HTTPError(400, "Missing content type")

        if ct != 'application/xml':
            raise cherrypy.HTTPError(415, 'Unsupported Media Type')

        return u'application/xml'

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
    # Object API
    ##########################################
    def add_profile(self, profile):
        collection = self.collection
        mimetype = u'application/xml'
        member = ProfileResource(collection, media_type=mimetype)
        member.generate(mimetype, source=profile, slug=profile.username)
        
        collection.attach(member, member_content=member.atom.xml())
        collection.store.commit(message='Adding %s' % member.member_id)
        
        collection.attach(member, media_content=profile.xml())
        collection.store.commit(message='Adding %s' % member.media_id)
        
        collection.feed_handler.set(collection.feed)

        return member

    def delete_profile(self, id):
        id = safe_unquote(id)
        member_id, media_id = self.collection.convert_id(id)
        member = self.collection.get_member(member_id)
        if member:
            self.collection.prune(member.member_id, member.media_id)
            self.collection.store.commit(message="Deleting %s and %s" % (member.member_id,
                                                                         member.media_id))
            
            # Regenerate the collection feed
            self.collection.feed_handler.set(self.collection.feed)
        
    ##########################################
    # AtomPub web service interface
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
    
    def retrieve_head(self, id=None):
        content = self.retrieve(id)
        cherrypy.response.headers['Content-Length'] = len(content)

    def create(self, profile):
        mimetype = self.__check_content_type()
        length = self.__check_length()
        
        member = self.add_profile(profile)

        cherrypy.response.status = '201 Created'
        member_uri = member.member_uri
        if member_uri:
            member_uri = member_uri.encode('utf-8')
            cherrypy.response.headers['Location'] = member_uri
            cherrypy.response.headers['Content-Location'] = member_uri
            
        cherrypy.response.headers['Content-Type'] = u'application/atom+xml;type=entry'
        cherrypy.response.headers['ETag'] = compute_etag_from_entry(member.atom)

        return member.xml(indent=True)
        
    def replace(self, id, profile):
        mimetype = self.__check_content_type()
        length = self.__check_length()
        member = self.__get_member(id)

        if not profile:
            raise cherrypy.HTTPError(400, 'Missing or invalid profile provided')

        if cherrypy.request.headers.get('If-Match'):
            try:
                handle_if_match(compute_etag_from_entry(member.atom),
                                cherrypy.request.headers.elements('If-Match') or [])
                # We want to prevent the CherryPy Etag tool to process this header
                # again and break the response
                del cherrypy.request.headers['If-Match']
            except ResourceOperationException, roe:
                raise cherrypy.HTTPError(roe.code, roe.msg)

        new_member = ProfileResource(self.collection, media_type=mimetype)
        content = new_member.generate(mimetype, source=profile, slug=profile.get('username', ''),
                                      existing_member=member, length=length)
        new_member.use_published_date_from(member) # let's keep the published date
        new_member.update_dates() # but update the other dates
        
        self.collection.attach(new_member, member_content=new_member.atom.xml())
        self.collection.store.commit(message='Updating %s' % new_member.member_id)

        self.collection.attach(new_member, media_content=profile.xml())
        self.collection.store.commit(message='Updating %s' % new_member.media_id)

        # Regenerate the collection feed
        self.collection.feed_handler.set(self.collection.feed)

        ProfileManager.store_profile(self.atompub, profile)

        cherrypy.response.headers['Content-Type'] = mimetype
        cherrypy.response.headers['ETag'] = compute_etag_from_entry(new_member.atom)
        return new_member.xml()

    def remove(self, id):
        self.delete_profile(id)
