# -*- coding: utf-8 -*-
import cherrypy
from microblog.web.oidtool import DEFAULT_SESSION_NAME

__all__ = ['OpenIDWebApplication']

class OpenIDWebApplication(object):
    def __init__(self, tpl_lookup):
        self.tpl_lookup = tpl_lookup

    def login(self):  
        tpl = self.tpl_lookup.get_template('signin.mako')
        return tpl.render(selectedview="#signin")

    def logout(self):
        del cherrypy.session[oidtool.DEFAULT_SESSION_NAME]
        return "Disconnected"

    def failure(self):
        info = cherrypy.session[oidtool.DEFAULT_SESSION_NAME]['info']
        return "Verification of %s failed." % info.identiy_url

    def cancelled(self):
        return "Verification cancelled"

    def error(self):
        return "An error happened during the authentication"
