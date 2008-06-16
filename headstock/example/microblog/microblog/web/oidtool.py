# -*- coding: utf-8 -*-

__version__ = "0.2"
__authors__ = ["Sylvain Hellegouarch (sh@defuze.org)"]
__date__ = "2008/05/15"
__copyright__ = """
Copyright (c) 2006, 2007, 2008 Sylvain Hellegouarch
All rights reserved.
"""
__license__ = """
Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:
 
     * Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
     * Redistributions in binary form must reproduce the above copyright notice, 
       this list of conditions and the following disclaimer in the documentation 
       and/or other materials provided with the distribution.
     * Neither the name of Sylvain Hellegouarch nor the names of his contributors 
       may be used to endorse or promote products derived from this software 
       without specific prior written permission.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

__doc__ = """OpenID tool for CherryPy 3"""

from cgi import escape

# Requires at least Python OpenID 1.1.2RC1
# http://www.openidenabled.com/resources/downloads/python-openid/
import openid
from openid.consumer import consumer
from openid.oidutil import appendArgs
from openid.cryptutil import randomString
from openid.extensions.sreg import SRegRequest, SRegResponse

# Requires at least Python Yadis 1.1.0RC1
# http://www.openidenabled.com/resources/downloads/python-openid/
from yadis.discover import DiscoveryFailure

# Requires at least Python URLJR 1.0.1
# http://www.openidenabled.com/resources/downloads/python-openid/
from urljr.fetchers import HTTPFetchingError

# Requires CP >= 3.0.0
import cherrypy

UNKNOWN = 0
PROCESSING = 1
AUTHENTICATED = 2

DEFAULT_SESSION_NAME = 'OpenIDTool'

__all__ = ['OpenIDTool']

class OpenIDResponse(object):
    def __init__(self):
        self.info = None
        self.sreg = None

class OpenIDTool:
    def __init__(self, store, base_auth_path, session_name=DEFAULT_SESSION_NAME):
        """
        This tool provides a fairly easy way to add a OpenID consumer to your CherryPy
        application.

        When receiving a request the following steps happened:

        1.a. If the request path starts with 'base_auth_path', the tool returns immediatly
        1.b. The tool looks for the openid_url parameters (either passed within the querystring
             or through the request body).
             a. If that parameter is not present the tool immediatly redirects to the login page
             b. If it is found then it redirects to the OpenID provider service
        2. When the provider service returns the tool checks if the authorization was given
           a. If not then it calls the appropriate error handler (failure, cancelled, error)
           b. If the authorization was successful then it processes as normal the requested
              page handler.

        At each step the current status of the processing is kept within the session so that
        we know where we stand whenever we received a request.

        Keyword arguments:
        store -- a Python OpenID store instance (check the OpenID documentation)
        
        base_auth_path -- base path of the objects containing page handlers for each step
        in the process (login, logout, failure, cancelled, error). Note that setting this
        value might be done differently in the future as the current practice is not
        really flexible.
        
        session_name -- name to give to the session node within the session object (when using
        a cookie this is the cookie name for instance)
        """
        self.store = store
        self.session_name = session_name
        self.base_auth_path = base_auth_path + '/'
        self.login_path = '%s/login' % base_auth_path
        self.failed_authentication_path = '%s/failure' % base_auth_path
        self.cancel_authentication_path = '%s/cancelled' % base_auth_path
        self.error_authentication_path = '%s/error' % base_auth_path
        self.return_to = None

    def force_return_to_url(self, path_info):
        self.return_to = path_info
        
    def get_session(self):
        oidsession = cherrypy.session.get(self.session_name, None)
        
        if not oidsession or not isinstance(oidsession, dict):
            oidsession = {}
            
        if 'sid' not in oidsession:
            sid = randomString(16, '0123456789abcdef')
            oidsession['sid'] = sid
            cherrypy.session[self.session_name] = oidsession
            cherrypy.session[self.session_name]['status'] = UNKNOWN
        
        return cherrypy.session[self.session_name]

    def is_processing(self):
        if cherrypy.session.has_key(self.session_name):
            if 'status' in cherrypy.session[self.session_name]:
                if cherrypy.session[self.session_name]['status'] in [PROCESSING, AUTHENTICATED]:
                    return True
        return False

    def is_authenticated(self):
        if cherrypy.session.has_key(self.session_name):
            if 'status' in cherrypy.session[self.session_name]:
                if cherrypy.session[self.session_name]['status'] == AUTHENTICATED:
                    return True
        return False

    def verify(self):
        """
        First part of the OpenID processing. We get the OpenID url and
        we redirect the user-agent to that url for authentication.
        """
        # If the requested path belongs to the one defined for the
        # connection handlers then we do not performany verification
        if cherrypy.request.path_info.startswith(self.base_auth_path):
            return
        
        cherrypy.request.openid = None
        # this method is always called so we check if we haven't already
        # been authenticated or if we are not in the middle of
        # the processing and leave silentely in such case
        if self.is_processing():
            if 'openid_url' in cherrypy.request.params:
                del cherrypy.request.params['openid_url']
            return 
        
        openid_url = cherrypy.request.params.get('openid_url', None)
        if not openid_url:
            raise cherrypy.HTTPRedirect(self.login_path)

        del cherrypy.request.params['openid_url']

        oidconsumer = consumer.Consumer(self.get_session(), self.store)
        try:
            request = oidconsumer.begin(openid_url)
            request.addExtension(SRegRequest(required=['email', 'nickname']))            
        except HTTPFetchingError, exc:
            # these could be more explicit maybe
            raise HTTPError(500, 'Error in discovery')
        except DiscoveryFailure, exc:
            # these could be more explicit maybe
            raise HTTPError(500, 'Error in discovery')
        else:
            if request is None:
                # these could be more explicit maybe
                raise HTTPError(500, 'No OpenID service found')
            else:
                # Then, ask the library to begin the authorization.
                # Here we find out the identity server that will verify the
                # user's identity, and get a token that allows us to
                # communicate securely with the identity server.
            
                return_to = self.return_to
                if not self.return_to:
                    return_to = cherrypy.url(cherrypy.request.path_info)
                redirect_url = request.redirectURL(cherrypy.request.base, return_to)

                cherrypy.session[self.session_name]['return_to'] = return_to
                cherrypy.session[self.session_name]['status'] = PROCESSING
                raise cherrypy.HTTPRedirect(redirect_url)

    def process(self):
        """
        Second part of the authentication. The OpenID provider service
        redirects to us with information in the URL regarding the status
        of the authentication on its side.
        """
        # If the requested path belongs to the one defined for the
        # connection handlers then we do not performany verification
        if cherrypy.request.path_info.startswith(self.base_auth_path):
            return
        
        # If we are already authenticated then we don't apply this step
        # any further
        if self.is_authenticated():
            info = cherrypy.session[self.session_name]['info']
            sreg = cherrypy.session[self.session_name]['sreg']
            cherrypy.request.openid = OpenIDResponse()
            cherrypy.request.openid.info = info
            cherrypy.request.openid.sreg = sreg
            return
        
        oidconsumer = consumer.Consumer(self.get_session(), self.store)

        cherrypy.session[self.session_name]['status'] = UNKNOWN
        cherrypy.request.openid = OpenIDResponse()
        
        # Ask the library to check the response that the server sent
        # us.  Status is a code indicating the response type. info is
        # either None or a string containing more information about
        # the return type.
        info = oidconsumer.complete(query=cherrypy.request.params,
                                    current_url=cherrypy.session[self.session_name]['return_to'])
        sreg = SRegResponse.fromSuccessResponse(info)
        cherrypy.session[self.session_name]['info'] = info
        cherrypy.session[self.session_name]['sreg'] = sreg

        cherrypy.request.openid.info = info
        cherrypy.request.openid.sreg = sreg
        
        if info.status == consumer.FAILURE and info.identity_url:
            # In the case of failure, if info is non-None, it is the
            # URL that we were verifying. We include it in the error
            # message to help the user figure out what happened.
            raise cherrypy.HTTPRedirect(self.failed_authentication_path)
        elif info.status == consumer.SUCCESS:
            # Success means that the transaction completed without
            # error. If info is None, it means that the user cancelled
            # the verification.
            
            # This is a successful verification attempt. If this
            # was a real application, we would do our login,
            # comment posting, etc. here.
            if info.endpoint.canonicalID:
                # You should authorize i-name users by their canonicalID,
                # rather than their more human-friendly identifiers.  That
                # way their account with you is not compromised if their
                # i-name registration expires and is bought by someone else.
                pass
            cherrypy.session[self.session_name]['status'] = AUTHENTICATED
            cherrypy.request.params = {}
            raise cherrypy.HTTPRedirect(cherrypy.url(cherrypy.request.path_info))
        elif info.status == consumer.CANCEL:
            # cancelled
            raise cherrypy.HTTPRedirect(self.cancel_authentication_path)
        
        raise cherrypy.HTTPRedirect(self.error_authentication_path)
        
    def _setup(self):
        # By setting these priorities we ensure that 'verify' will be performed
        # before 'process'.
        cherrypy.request.hooks.attach('before_request_body', self.verify, priority=63)
        cherrypy.request.hooks.attach('before_request_body', self.process, priority=64)
