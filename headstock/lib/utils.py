# -*- coding: utf-8 -*-
import codecs
try:
    from hashlib import sha
except ImportError:
    from sha import new as sha
from time import time
from random import random


__all__ = ['generate_unique', 'remove_BOM']

def generate_unique(seed=None):
    if not seed:
        seed = str(time() * random())
    return unicode(abs(hash(sha(seed).hexdigest())))

def remove_BOM(text):
    if codecs.BOM_UTF8.decode("utf-8") in text:
        return text.replace(codecs.BOM_UTF8.decode("utf-8"), '')
    if codecs.BOM.decode("utf-16") in text:
        return text.replace(codecs.BOM.decode("utf-16"), '')
    if codecs.BOM_BE.decode("utf-16-be") in text:
        return text.replace(codecs.BOM_BE.decode("utf-16-be"), '')
    if codecs.BOM_LE.decode("utf-16-le") in text:
        return text.replace(codecs.BOM_LE.decode("utf-16-le"), '')

    return text
