# -*- coding: utf-8 -*-
import os.path

import cherrypy

from microblog.web import MICROBLOG_SESSION_PROFILE
from microblog.web.oidtool import DEFAULT_SESSION_NAME
from microblog.profile.manager import ProfileManager

__all__ = ['SpeakUpWebApplication']

class SpeakUpWebApplication(object):
    _cp_config = {'tools.openid.on': False}

    def __init__(self, base_dir, atompub, tpl_lookup, profile, collection_handler):
        self.base_dir = base_dir
        self.atompub = atompub
        self.tpl_lookup = tpl_lookup
        self.profile = profile
        self.collection_handler = collection_handler
        
    def index(self):
        tpl = self.tpl_lookup.get_template('userindex.mako')
        return tpl.render(profile=self.profile, 
                          member=self.collection_handler.most_recent_member,
                          collection=self.collection_handler.collection)
