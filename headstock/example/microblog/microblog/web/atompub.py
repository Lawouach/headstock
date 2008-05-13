# -*- coding: utf-8 -*-

import cherrypy
import time
import os

from amplee.atompub.collection import FeedHandler
from amplee.loader import AtomPubLoader
from amplee.error import ResourceOperationException
from amplee.utils.mediatype import get_best_mimetype
from amplee.atompub.member import MemberResource
from amplee.atompub.workspace import *
from amplee.atompub.collection import *
from amplee.utils import get_isodate, generate_uuid_uri, \
     compute_etag_from_feed, compute_etag_from_entry, \
     decode_slug, handle_if_match, safe_unquote, \
     extract_media_type, extract_url_trail, \
     safe_url_join, extract_url_path_info, qname

def _amplee_process_request_body():
    # We do not want CherryPy to handle the request body
    # as we will always simply read the content no matter
    # what. The following two lines achieve this.
    cherrypy.request.body = cherrypy.request.rfile
    cherrypy.request.process_request_body = False

# We set the previous function as a tool that we can
# enable for the Store 
cherrypy.tools.amplee_request_body = cherrypy.Tool('before_request_body',
                                                   _amplee_process_request_body)

__all__ = ['Application', 'ResourceWrapper']

class Application(object):
    def __init__(self, base_dir, index, dispatcher):
        apl = AtomPubLoader(base_dir)
        self.base_dir = base_dir
        self.servdoc, self.xmldoc = apl.load(os.path.join(base_dir, 'config.xml'),
                                             os.path.join(base_dir, 'service.xml'))

        self.indexer = index
        self.dispatcher = dispatcher
        self.complete_service_loading()
        self.attach_serving_service_application()

        cherrypy.log('AtomPub service application ready')
        
    def complete_service_loading(self):
        # When a service is loaded from a service document
        # some information must be set manually after the loading process
        # as they couldn't be guessed by amplee
        
        for collection in self.servdoc.get_collections():
            self.setup_collection(collection)

    def setup_collection(self, collection):
        # Because the service loader doesn't have the notiuon
        # of an id for the collection, we first need to
        # create one. For this example, we use the path info
        # at which the collection can be located
        pi = extract_url_path_info(collection.get_base_edit_uri()).strip('/')
        collection.name_or_id = pi

        # Next we use that id to ensure the repository structure
        # is correctly created
        collection.store.storage.create_container(pi)
        collection.store.media_storage.create_container(pi)

        # Set the index
        collection.add_indexer(self.indexer)

        # We indicate what class needs to be used when loading members
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

        self.attach_serving_collection_application(collection, pi)

    def attach_serving_service_application(self):
        controller = ServiceHandler(self.servdoc.to_service().xml(indent=True))
        self.dispatcher.connect('service', route='service', controller=controller,
                                action='GET', conditions=dict(method=['GET']))
        self.dispatcher.connect('service', route='service', controller=controller,
                                action='HEAD', conditions=dict(method=['HEAD']))

    def attach_serving_collection_application(self, c, path):
        controller = CollectionHandler(c)
        self.dispatcher.connect('controller_%s' % path, route=path, controller=controller,
                                action='GET', conditions=dict(method=['GET']))
        self.dispatcher.connect('controller_%s' % path, route=path, controller=controller,
                                action='POST', conditions=dict(method=['POST']))
        self.dispatcher.connect('controller_%s' % path, route=path, controller=controller,
                                action='PUT', conditions=dict(method=['PUT']))
        self.dispatcher.connect('controller_%s' % path, route=path, controller=controller,
                                action='DELETE', conditions=dict(method=['DELETE']))

        controller = CollectionPagingHandler(c)
        self.dispatcher.connect('controller_%s_paging' % path, route='%s/paging' % path, 
                                controller=controller, action='GET', conditions=dict(method=['GET']))
    

    def retrieve_collection(self, name):
        return self.servdoc.get_collection(name.strip('/'))
        

    def add_collection(self, path):
        path = path.strip('/')
        basepath, collection_name = path.rsplit('/', 1)
        workspace = AtomPubWorkspace(self.servdoc, basepath, title=basepath)
        c = AtomPubCollection(workspace, name_or_id=path, title=collection_name,
                              base_uri=path, base_edit_uri=path,
                              accept_media_types=u'application/atom+xml;type=entry')
        self.setup_collection(c)
        self.attach_serving_collection_application(c)

        # Let's save this to the service document
        file(os.path.join(self.base_dir, 'service.xml'), 'wb').write(self.servdoc.to_service().xml(indent=True))

        return c

    def index(self):
        return "microblogging"

class ServiceHandler(object):
    def __init__(self, servdoc):
        self.servdoc = servdoc

    def HEAD(self, *args, **kwargs):
        content = self.GET(*args, **kwargs)
        cherrypy.response.headers['Content-Length'] = len(content)

    def GET(self):
        cherrypy.response.headers['Content-Type'] = 'application/atomsvc+xml'
        return self.servdoc

class ResourceWrapper(MemberResource):
    def generate_resource_id(self, entry=None, slug=None, info=None):
        if slug:
            return slug.replace(' ','_').decode('utf-8')
        else:
            # if not then we use the last segment of the
            # link as the id of the resource in the storage
            links = entry.xml_xpath('/atom:entry/atom:link[@rel="edit"]')
            if links:
                return extract_url_trail(links[0].href)

        # fallback
        return str(time.time())

class DummyHandler(object):
    pass

class CollectionHandler(object):
    exposed = True
    _cp_config = {'tools.amplee_request_body.on': True}
    
    def __init__(self, collection):
        self.collection = collection

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
    def GET(self, id=None):
        if id == None:
            collection_feed = self.collection.feed_handler.retrieve()
            cherrypy.response.headers['etag'] = compute_etag_from_feed(collection_feed)
            cherrypy.response.headers['content-type'] = 'application/atom+xml;type=feed'
            return self.collection.feed_handler.collection_xml()

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
    
    def HEAD(self, id=None):
        content = self.GET(id)
        cherrypy.response.headers['Content-Length'] = len(content)

    def POST(self):
        mimetype = self.__check_content_type()
        length = self.__check_length()
        slug = decode_slug(cherrypy.request.headers.get('slug', None))
        
        member = ResourceWrapper(self.collection, media_type=mimetype)
        content = member.generate(mimetype, source=cherrypy.request.body, slug=slug,
                                  length=length, preserve_dates=False)
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

        return member.xml(indent=True)
        
    def PUT(self, id):
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

    def DELETE(self, id):
        member = self.__get_member(id)
        self.collection.prune(member.member_id, member.media_id)
        self.collection.store.commit(message="Deleting %s and %s" % (member.member_id,
                                                                     member.media_id))
        
        # Regenerate the collection feed
        self.collection.feed_handler.set(self.collection.feed)

class CollectionPagingHandler(object):
    exposed = True
    
    def __init__(self, collection):
        self.collection = collection

    def GET(self, start=0):
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
