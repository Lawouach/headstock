# -*- coding: utf-8 -*-
import cherrypy
from headstock.api.profile import Profile
from bridge import Element as E

from microblog.profile.user import UserProfile

def _amplee_process_request_body():
    # We do not want CherryPy to handle the request body
    # as we will always simply read the content no matter
    # what. The following two lines achieve this.
    if cherrypy.request.method in ['POST', 'PUT']:
        cherrypy.request.body = cherrypy.request.rfile
        cherrypy.request.process_request_body = False

cherrypy.tools.amplee_request_body = cherrypy.Tool('before_request_body',
                                                   _amplee_process_request_body)

def _profile_process_request_body():
    if cherrypy.request.method in ['POST', 'PUT']:
        cherrypy.request.process_request_body = False
        length = cherrypy.request.headers.get('content-length', 0)
        if not length:
            cherrypy.request.params['profile'] = None
            return

        cherrypy.request.params['profile'] = None
        content = cherrypy.request.rfile.read(int(length))
        profile = Profile.from_profile_element(E.load(content).xml_root)
        field = profile.x.field_by_var('nickname')
        if field and field.values:
            profile_name = field.values[0]
            cherrypy.request.params['profile'] = UserProfile(profile_name, profile)

cherrypy.tools.user_profile_parser = cherrypy.Tool('before_request_body',
                                                   _profile_process_request_body)
