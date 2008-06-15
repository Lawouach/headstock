# -*- coding: utf-8 -*-
import sys
import os
import tempfile

import cherrypy
from selector4cherrypy import SelectorDispatcher
from openid.store import filestore

from mako.template import Template
from mako.lookup import TemplateLookup
    
import microblog.web.profiletool
from microblog.web.oidtool import OpenIDTool
from microblog.web.application import WebApplication
from microblog.web.oid import OpenIDWebApplication
from microblog.web.atompub import AtomPubWebApplication
from microblog.web.profile import UserProfileAtomPubWebApplication
from microblog.profile.manager import ProfileManager

from microblog.atompub.application import AtomPubApplication

base_dir = os.getcwd()

class Server(object):
    def __init__(self):
        self.setup_mako()
        self.setup_atompub()
        self.setup_profiles()
        self.setup_openid()
        self.setup_web()
        self.setup_cherrypy()

    def run(self):
        cherrypy.engine.start()
        cherrypy.engine.block()

    def setup_cherrypy(self):   
        cherrypy.config.update({'engine.autoreload_on' : False,
                                'server.socket_port' : 8080, 
                                'server.socket_host': '127.0.0.1',
                                'server.socket_queue_size': 15,
                                'log.screen': True,
                                'log.access_file': os.path.join(base_dir, 'logs', 'http_access.log'),
                                'log.error_file': os.path.join(base_dir, 'logs', 'http_error.log'),
                                'checker.on': False,})
        d = SelectorDispatcher()
        d.add('/service[/]', GET=self.atompubapp.service_get, 
              HEAD=self.atompubapp.service_head)

        # OpenID controllers
        d.add('/auth/login', GET=self.oidapp.login)
        d.add('/auth/logout', GET=self.oidapp.logout)
        d.add('/auth/failure', GET=self.oidapp.failure)
        d.add('/auth/error', GET=self.oidapp.error)
        d.add('/auth/cancelled', GET=self.oidapp.cancelled)

        # New profiles controllers
        d.add('/profile/new/feed', GET=self.newprofileapp.feed)
        d.add('/profile/new/', POST=self.newprofileapp.create)
        d.add('/profile/new/{id}', GET=self.newprofileapp.retrieve, 
              HEAD=self.newprofileapp.retrieve_head,
              PUT=self.newprofileapp.replace,
              DELETE=self.newprofileapp.remove)

        # Profiles controllers
        d.add('/profile/feed', GET=self.existingprofileapp.feed)
        d.add('/profile/', POST=self.existingprofileapp.create)
        d.add('/profile/{id}', GET=self.existingprofileapp.retrieve,
              HEAD=self.existingprofileapp.retrieve_head,
              PUT=self.existingprofileapp.replace,
              DELETE=self.existingprofileapp.remove)

        # Main web application controllers
        d.add('/signin[/]', GET=self.webapp.signin)
        d.add('/signup[/]', GET=self.webapp.signup)
        d.add('/signup/complete', POST=self.webapp.signup_complete)
        d.add('/signout[/]', GET=self.webapp.signout)
        d.add('/', GET=self.webapp.index)

        for profile_name in self.profiles:
            p = self.profiles[profile_name]
            c = self.atompub.service.get_collection_by_xml_id('collection-%s' % profile_name)
            self.webapp.attach_serving_collection_application(c, p, d)

        conf = {'/': { 'request.dispatch': d,
                       'tools.etags.on': True,
                       'tools.etags.autotags': True,
                       'tools.sessions.on': True,
                       'tools.sessions.storage_type': 'memcached',},
                '/signup': {'tools.openid.on': True,},
                '/profile/feed': {'tools.openid.on': False,
                                  'tools.etags.on': True,
                                  'tools.etags.autotags': True,},
                '/profile/new': {'tools.openid.on': False,
                                 'tools.etags.on': True,
                                 'tools.etags.autotags': False,},
                '/js': {'tools.openid.on': False,
                        'tools.staticdir.on': True,
                        'tools.staticdir.dir': os.path.join(base_dir, 'design', 
                                                            'default', 'js')},
                '/images': {'tools.openid.on': False,
                            'tools.staticdir.on': True,
                            'tools.staticdir.dir': os.path.join(base_dir, 'design', 
                                                                'default', 'images')},
                '/css': {'tools.openid.on': False,
                         'tools.staticdir.on': True,
                         'tools.staticdir.dir': os.path.join(base_dir, 'design', 
                                                             'default', 'css')}}


        cherrypy.tree.mount(self.webapp, '/', conf)

    def setup_web(self):
        self.webapp = WebApplication(base_dir, self.atompub, self.tpl_lookup)
        self.oidapp = OpenIDWebApplication(self.tpl_lookup)
        self.atompubapp = AtomPubWebApplication(base_dir, self.atompub, self.tpl_lookup)
        
        collection = self.atompub.service.get_collection_by_xml_id('collection-profile')
        self.existingprofileapp = UserProfileAtomPubWebApplication(base_dir, self.atompub, 
                                                                   collection, self.tpl_lookup)
        collection = self.atompub.service.get_collection_by_xml_id('collection-profile-new')
        self.newprofileapp = UserProfileAtomPubWebApplication(base_dir, self.atompub, 
                                                              collection, self.tpl_lookup)
        self.webapp.new_profiles_atompub_app = self.newprofileapp
        self.webapp.profiles_atompub_app = self.newprofileapp

    def setup_profiles(self):
        self.profiles = ProfileManager.load_profiles(base_dir, self.atompub)

    def setup_atompub(self):
        self.atompub = AtomPubApplication(base_dir)
        
    def setup_openid(self):
        store = filestore.FileOpenIDStore(tempfile.gettempdir())
        cherrypy.tools.openid = OpenIDTool(store, '/auth')

    def setup_mako(self):
        tpl_directory = os.path.join(base_dir, 'design', 'default', 'templates')
        tpl_cache_directory = os.path.join(tpl_directory, 'cache')
        
        self.tpl_lookup = TemplateLookup(directories=[tpl_directory], 
                                         module_directory=tpl_cache_directory, 
                                         collection_size=70)


if __name__ == '__main__':
    s = Server()
    s.run()
