#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
from headstock.error import HeadstockAuthenticationFailure

__all__ = ['generate_credential', 'validate_credentials']

def generate_credential(authzid, authcid, password):
    return unicode(base64.b64encode('%s\x00%s\x00%s' % (authzid, authcid, password)))

def validate_credentials(b64_token):
    decoded_token = base64.b64decode(b64_token)
    try:
        authzid, authcid, password = decoded_token.split('\x00')
        return authzid, authcid, password
    except:
        raise HeadstockAuthenticationFailure()
