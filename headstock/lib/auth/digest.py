#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Partly implements: http://www.faqs.org/rfcs/rfc2831.html

# Code widely inspired from the httpauth module by
# Tiago Cogumbreiro and available at
# http://trac.defuze.org/browser/oss/httpauthfilter

import base64
import md5
import sha
import random

H = lambda val: md5.new(val).digest()
HH = lambda val: md5.new(val).hexdigest()

def _challenge_to_dict(challenge):
    decoded = base64.b64decode(challenge)
    params = {}
    tokens = decoded.split(',')
    for token in tokens:
        key, value = token.split('=')
        params[key] = value.replace('"', '')

    return params

def _A1(params, username, password, **kwargs):
        # This is A1 if qop is set
        # A1 = H( unq(username-value) ":" unq(realm-value) ":" passwd )
        #         ":" unq(nonce-value) ":" unq(cnonce-value)
        h_a1 = H('%s:%s:%s' % (username, params["realm"], password))
        h_a1 = '%s:%s:%s' % (h_a1, params["nonce"], kwargs["cnonce"])
        authzid = kwargs.get('authzid', None)
        if authzid:
            h_a1 = "%s:%s" % (h_a1, authzid)
        return h_a1

def _A2(params, digest_uri):
    qop = params.get("qop", "auth")
    if qop == 'auth':
        # If the "qop" directive's value is "auth", then A2 is
        return "AUTHENTICATE:%s" % digest_uri
    elif qop in ('auth-int', 'auth-conf'):
        # If the "qop" value is "auth-int" or "auth-conf" then A2 is
        return "AUTHENTICATE:%s:00000000000000000000000000000000" % digest_uri
    else:
        raise NotImplementedError ("The 'qop' method is unknown: %s" % qop)

def compute_digest_response(challenge, username, password, **kwargs):
    """
    Computes and returns an encoded (base64) string based on the challenge and input values.

    Keyword arguments:
    challenge -- encoded string sent by the XMPP component/server
    username -- username string
    password -- password string

    Common additional keyword arguments should be:
    digest_uri -- a string of the form : 'xmpp/hostname' where hostname is the
    name of the remote host
    cnonce -- unique value identifying this exchange (if not provided a default one
    will be computed)
    nc -- count of number of requests made so far by the client (default to '00000001')
    """
    params = _challenge_to_dict(challenge)
    
    algorithm = params.get("algorithm", 'md5-sess')
    if algorithm is None:
        raise ValueError, "Missing 'algorithm' token within challenge"
    
    digest_uri = params.get('digest-uri', kwargs.get('digest_uri', None))
    if not digest_uri:
        raise ValueError, "Missing 'digest-uri' token within challenge"

    realm = params.get('realm', '')
    params['realm'] = realm
    
    charset = params.get('charset', None)
    # If not present, the username and password must be encoded in ISO 8859-1
    encode_as = charset or 'ISO 8859-1'
    
    if isinstance(username, unicode):
        username = username.encode(encode_as)

    if isinstance(password, unicode):
        password = password.encode(encode_as)

    if charset and charset.lower() != 'utf-8':
        # The client should send this directive only
        # if the server has indicated it supports UTF-8. 
        charset = None

    if 'nc' not in kwargs:
        kwargs['nc'] = '00000001'

    if 'cnonce' not in kwargs:
        random.seed()
        kwargs['cnonce'] = hex(int(random.random() * 26804224))[2:]

    H_A1 = HH(_A1(params, username, password, **kwargs))
    H_A2 = HH(_A2(params, digest_uri))

    qop = params.get("qop", 'auth')
    nonce = params['nonce']
    nc = kwargs['nc']
    cnonce = kwargs['cnonce']
    nonce = params['nonce']
    
    response = HH("%s:%s:%s:%s:%s:%s" % (H_A1, nonce, nc, cnonce, qop, H_A2))
    request = 'username="%s",realm="%s",nonce="%s",cnonce="%s",nc=%s,' % (username, realm, nonce, cnonce, nc)
    request = request + 'qop=%s,digest-uri="%s",response=%s' % (qop, digest_uri, response)

    if charset is not None:
        request = request + ',charset=%s' % charset

    return base64.b64encode(request).decode('utf-8')
