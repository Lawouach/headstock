#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sha
import time

def generate_unique():
    return unicode(abs(hash(sha.new(str(time.time())).hexdigest())))
