#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Partly implements: http://www.faqs.org/rfcs/rfc2831.html

# Code widely inspired from the httpauth module by
# Tiago Cogumbreiro and available at
# http://trac.defuze.org/browser/oss/httpauthfilter

import base64
import md5
import sha
import random

from headstock.error import HeadstockAuthenticationFailure

__all__ = ['compute_rspauth', 'generate_challenge', \
           'challenge_to_dict', 'compute_digest_response', \
           'validate_response']

H = lambda val: md5.new(val).digest()
HH = lambda val: md5.new(val).hexdigest()

def generate_challenge():
    return base64.b64encode('nonce="%d",qop="auth",charset=utf-8,algorithm=md5-sess' % int(random.random() * 26804224)).decode('utf-8')

def challenge_to_dict(challenge):
    decoded = base64.b64decode(challenge)
    params = {}
    tokens = decoded.split(',')
    for token in tokens:
        key, value = token.split('=', 1)
        params[key] = value.replace('"', '')

    return params

def _A1(params, username, password, **kwargs):
        # This is A1 if qop is set
        # A1 = H( unq(username-value) ":" unq(realm-value) ":" passwd )
        #         ":" unq(nonce-value) ":" unq(cnonce-value)
        h_a1 = H('%s:%s:%s' % (username, params["realm"], password))
        h_a1 = '%s:%s:%s' % (h_a1, params.get("nonce", ''), kwargs["cnonce"])
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

def _A2_rspauth(params, digest_uri):
    qop = params.get("qop", "auth")
    if qop == 'auth':
        # If the "qop" directive's value is "auth", then A2 is
        return ":%s" % digest_uri
    elif qop in ('auth-int', 'auth-conf'):
        # If the "qop" value is "auth-int" or "auth-conf" then A2 is
        return ":%s:00000000000000000000000000000000" % digest_uri
    else:
        raise NotImplementedError ("The 'qop' method is unknown: %s" % qop)

def compute_digest_response(params, username, password, **kwargs):
    """
    Computes and returns an encoded (base64) string based on the challenge and input values.

    Keyword arguments:
    params -- decode challenge as a dictionnary
    username -- username string
    password -- password string

    Common additional keyword arguments should be:
    digest_uri -- a string of the form : 'xmpp/hostname' where hostname is the
    name of the remote host
    cnonce -- unique value identifying this exchange (if not provided a default one
    will be computed)
    nc -- count of number of requests made so far by the client (default to '00000001')
    """
    algorithm = params.get("algorithm", None)
    if algorithm is None:
        raise ValueError("Missing 'algorithm' token within challenge")

    if algorithm != 'md5-sess':
        raise ValueError("Unsupported digest algorithm: %s" % algorithm)
    
    digest_uri = params.get('digest-uri', kwargs.get('digest_uri', None))
    if not digest_uri:
        raise ValueError("Missing 'digest-uri' token within challenge")

    realm = params['realm'] = params.get('realm', '')
    
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
    nonce = params.get('nonce', '')
    nc = kwargs['nc']
    cnonce = kwargs['cnonce']
    
    response = HH("%s:%s:%s:%s:%s:%s" % (H_A1, nonce, nc, cnonce, qop, H_A2))
    request = 'username="%s",realm="%s",nonce="%s",cnonce="%s",nc=%s,' % (username, realm, nonce, cnonce, nc)
    request = request + 'qop=%s,digest-uri="%s",response=%s' % (qop, digest_uri, response)

    if charset is not None:
        request = request + ',charset=%s' % charset

    return base64.b64encode(request).decode('utf-8')

def validate_response(response, password):
    """
    Raises HeadstockAuthenticationFailure if the response is not valid.

    Keyword arguments:
    response -- encoded string returned by the client
    password -- password string stored on the server side
    """
    params = challenge_to_dict(response)
    
    digest_uri = params.get('digest-uri', None)
    if not digest_uri:
        raise HeadstockAuthenticationFailure("Missing 'digest-uri' token in response")

    realm = params['realm'] = params.get('realm', '')
    
    charset = params.get('charset', None)
    # If not present, the username and password must be encoded in ISO 8859-1
    encode_as = charset or 'ISO 8859-1'
    
    if isinstance(password, unicode):
        password = password.encode(encode_as)

    if charset and charset.lower() != 'utf-8':
        # The client should send this directive only
        # if the server has indicated it supports UTF-8. 
        charset = None

    if 'nc' not in params:
        raise HeadstockAuthenticationFailure("Missing 'nc' token") 

    H_A1 = HH(_A1(params, password=password, **params))
    H_A2 = HH(_A2(params, digest_uri))

    qop = params.get("qop", 'auth')
    nonce = params.get('nonce', '')
    nc = params['nc']
    cnonce = params['cnonce']
    username = params['username']
    
    rsp = HH("%s:%s:%s:%s:%s:%s" % (H_A1, nonce, nc, cnonce, qop, H_A2))
    
    if params['response'] != rsp:
        raise HeadstockAuthenticationFailure()

def compute_rspauth(response, password):
    """
    Computes the rspauth token to acknowledge the server validated the response.

    Keyword arguments:
    response -- encoded string returned by the client
    password -- password string stored on the server side
    """
    params = challenge_to_dict(response)
    algorithm = params.get("algorithm", 'md5-sess')
    if algorithm is None:
        raise ValueError("Missing 'algorithm' token in response")
    
    if algorithm != 'md5-sess':
        raise ValueError("Unsupported digest algorithm: %s" % algorithm)
    
    digest_uri = params.get('digest-uri', None)
    if not digest_uri:
        raise ValueError("Missing 'digest-uri' token in response")

    realm = params['realm'] = params.get('realm', '')
    
    charset = params.get('charset', None)
    # If not present, the username and password must be encoded in ISO 8859-1
    encode_as = charset or 'ISO 8859-1'
    
    if isinstance(password, unicode):
        password = password.encode(encode_as)

    if charset and charset.lower() != 'utf-8':
        # The client should send this directive only
        # if the server has indicated it supports UTF-8. 
        charset = None

    if 'nc' not in params:
        raise ValueError("Missing 'nc' token") 

    H_A1 = HH(_A1(params, password=password, **params))
    H_A2 = HH(_A2_rspauth(params, digest_uri))

    qop = params.get("qop", 'auth')
    nonce = params.get('nonce', '')
    nc = params['nc']
    cnonce = params['cnonce']
    username = params['username']
    
    return base64.b64encode('rspauth="%s"' % HH("%s:%s:%s:%s:%s:%s" % (H_A1, nonce, nc, cnonce, qop, H_A2))).decode('utf-8')
