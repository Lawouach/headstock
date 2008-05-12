#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sha
from time import time
from random import random

__all__ = ['generate_unique']

def generate_unique(seed=None):
    if not seed:
        seed = str(time() * random())
    return unicode(abs(hash(sha.new(seed).hexdigest())))
