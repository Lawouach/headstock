#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Implements http://code.google.com/apis/accounts/AuthForInstalledApps.html
# Inspired from httplib2

import base64
from urllib2 import urlopen, URLError, HTTPError
from urllib import urlencode

GOOGLE_CLIENT_LOGIN_URL = 'https://www.google.com/accounts/ClientLogin'

__all__ = ['perform_authentication']

def perform_authentication(email, password, service='cl', source=None):
    data = {'Email': email, 'Passwd': password, 'service': service}
    if source:
        data['source'] = source

    f = urlopen(GOOGLE_CLIENT_LOGIN_URL, urlencode(data))

    if f.code == 200:
        body = f.read().split('\n')
        d = dict([tuple(line.split("=", 1)) for line in body if line])
        
        return unicode(base64.b64encode('\x00%s\x00%s' % (email, d['Auth'])))

    return None
