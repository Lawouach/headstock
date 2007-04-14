#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64

__all__ = ['generate_credential']

def generate_credential(authzid, authcid, password):
    return unicode(base64.b64encode('%s\x00%s\x00%s' % (authzid, authcid, password)))
