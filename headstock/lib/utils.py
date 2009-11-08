# -*- coding: utf-8 -*-
import codecs
try:
    from hashlib import sha1 as sha
except ImportError:
    from sha import new as sha
from time import time
from random import random

__all__ = ['generate_unique', 'remove_BOM',
           'compute_handshake', 'parse_commandline']

def generate_unique(seed=None):
    """
    Generates a random and pseudo-unique string.

    ``seed`` None - if `None` the seed is generated
    from the current time and a random value.
    """
    if not seed:
        seed = str(time() * random())
    return unicode(abs(hash(sha(seed).hexdigest())))

def compute_handshake(stanza_id, secret):
    """
    Computes the SASL handshake

    ``stanza_id`` stanza identifier

    ``secret`` the secret value to be hashed with the stanza identifier.
    """
    return unicode(sha(str(stanza_id) + str(secret)).hexdigest().lower())

def remove_BOM(text):
    """
    Removes the BOM from the provided `text`.
    """
    if codecs.BOM_UTF8.decode("utf-8") in text:
        return text.replace(codecs.BOM_UTF8.decode("utf-8"), '')
    if codecs.BOM.decode("utf-16") in text:
        return text.replace(codecs.BOM.decode("utf-16"), '')
    if codecs.BOM_BE.decode("utf-16-be") in text:
        return text.replace(codecs.BOM_BE.decode("utf-16-be"), '')
    if codecs.BOM_LE.decode("utf-16-le") in text:
        return text.replace(codecs.BOM_LE.decode("utf-16-le"), '')

    return text

def parse_commandline():
    """
    Helper to parse the command line. Useful for quick
    client mockup.
    """
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-a", "--address", dest="address", action="store",
                       help="XMPP server address (default: localhost:5222) ")
    parser.set_defaults(address='localhost:5222')
    parser.add_option("-j", "--jid", dest="jid",
                      help="XMPP jid", action="store")
    parser.set_defaults(username=None)
    parser.add_option("-p", "--password", action="store", dest="password",
                      help="XMPP password. You may also be prompted for it if you do not pass this parameter")
    parser.set_defaults(password=None)
    parser.add_option("-r", "--register", action="store_true", dest="register",
                      help="Register the user if the server supports in-band registration (default: False)")
    parser.set_defaults(register=False)
    parser.add_option("-t", "--usetls", dest="usetls", action="store_true",
                       help="Use TLS (default: False)")
    parser.set_defaults(usetls=False)
    (options, args) = parser.parse_args()

    return options
