# -*- coding: utf-8 -*-
import cherrypy
from microblog.web import MICROBLOG_SESSION_PROFILE
from microblog.web.oidtool import DEFAULT_SESSION_NAME
from microblog.profile.manager import ProfileManager
from microblog.profile.user import EmptyUserProfile, UserProfile
from microblog.web.speakup import SpeakUpWebApplication
from microblog.web.atompub import CollectionHandler, CollectionPagingHandler

__all__ = ['WebApplication']

class WebApplication(object):
    def __init__(self, base_dir, atompub, tpl_lookup):
        self.base_dir = base_dir
        self.atompub = atompub
        self.tpl_lookup = tpl_lookup
        
        self.new_profiles_atompub_app = None
        self.profiles_atompub_app = None

    def index(self):
        profile = cherrypy.session.get(MICROBLOG_SESSION_PROFILE, None)
        if not profile:
            tpl = self.tpl_lookup.get_template('welcome.mako')
            return tpl.render()
         
        cherrypy.session[MICROBLOG_SESSION_PROFILE] = profile 
        tpl = self.tpl_lookup.get_template('index.mako')
        return tpl.render(profile=profile)

    def signin(self):
        tpl = self.tpl_lookup.get_template('signin.mako')
        return tpl.render()

    @cherrypy.tools.profile_required()
    def signout(self):
        del cherrypy.session[MICROBLOG_SESSION_PROFILE]
        if DEFAULT_SESSION_NAME in cherrypy.session:
            del cherrypy.session[DEFAULT_SESSION_NAME]
        cherrypy.request.openid = None
        if hasattr(cherrypy.request, 'microblog'):
            delattr(cherrypy.request, 'microblog')

        raise cherrypy.HTTPRedirect('/')

    def signup(self):
        username = cherrypy.request.openid.sreg.get('nickname', '')
        username = username.strip()
        cherrypy.session['creationprocess'] = True
        tpl = self.tpl_lookup.get_template('newaccount_step2.mako')
        return tpl.render(username=username)

    def signup_complete(self, username):
        username = username.strip()

        valid = True
        if not username:
            valid = False
            
        if ProfileManager.has_profile(self.atompub, username):
            valid = False
            
        if not valid:
            tpl = self.tpl_lookup.get_template('newaccount_step2.mako')
            return tpl.render(username=username, error="Username already taken")

        profile = UserProfile(username)
        profile.fill(nickname=username)

        ProfileManager.store_profile(self.atompub, profile)
        cherrypy.session[MICROBLOG_SESSION_PROFILE] = profile
        if cherrypy.request.openid:
            oid = cherrypy.request.openid.info.identity_url
            cherrypy.session[oid] = profile

        w = self.atompub.add_workspace(profile.username)
        c = self.atompub.add_collection(w, profile.username)
        self.atompub.save_service()
        self.attach_serving_collection_application(c, profile,
                                                   d = cherrypy.request.dispatch)

        self.new_profiles_atompub_app.add_profile(profile)
        self.profiles_atompub_app.add_profile(profile)

        raise cherrypy.HTTPRedirect('/%s' % profile.username)

    def attach_serving_collection_application(self, c, profile, d):
        profile_name = profile.username
        controller = CollectionHandler(c)
        route = '/%s' % profile_name.encode('utf-8')
        speakup = SpeakUpWebApplication(self.base_dir, self.atompub, 
                                        self.tpl_lookup, profile, controller)

        d.add('%s[/]' % route, GET=speakup.index,
              POST=controller.create)
        d.add('%s/feed' % route, GET=controller.feed)
        d.add('%s/{id:any}' % route, GET=controller.retrieve,
              PUT=controller.replace,
              DELETE=controller.remove)

        controller = CollectionPagingHandler(c)
        d.add('%s/paging' % route, GET=controller.GET)
