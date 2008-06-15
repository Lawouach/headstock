# -*- coding: utf-8 -*-
import codecs
import sha
from time import time
from random import random


__all__ = ['generate_unique', 'remove_BOM']

def generate_unique(seed=None):
    if not seed:
        seed = str(time() * random())
    return unicode(abs(hash(sha.new(seed).hexdigest())))

def remove_BOM(text):
    if text[0] == codecs.BOM_UTF8.decode("utf-8"):
        return text.replace(codecs.BOM_UTF8.decode("utf-8"), '')
    if text[0] == codecs.BOM.decode("utf-16"):
        return text.replace(codecs.BOM.decode("utf-16"), '')
    if text[0] == codecs.BOM_BE.decode("utf-16-be"):
        return text.replace(codecs.BOM_BE.decode("utf-16-be"), '')
    if text[0] == codecs.BOM_LE.decode("utf-16-le"):
        return text.replace(codecs.BOM_LE.decode("utf-16-le"), '')

    return text
