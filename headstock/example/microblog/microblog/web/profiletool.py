# -*- coding: utf-8 -*-
import cherrypy
from microblog.web import Microblog, MICROBLOG_SESSION_PROFILE

def _profile_required():
    profile = cherrypy.session.get(MICROBLOG_SESSION_PROFILE, None)
    if not profile:
        raise cherrypy.HTTPRedirect('/signin')

    cherrypy.request.microblog = Microblog()
    cherrypy.request.microblog.profile = profile

cherrypy.tools.profile_required = cherrypy.Tool('before_request_body',
                                                _profile_required, priority=70)
