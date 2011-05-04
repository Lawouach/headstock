#!/usr/bin/env python

import unittest
from headstock.lib.jid import JID

class TestJID(unittest.TestCase):

    def setUp(self):
        self.jid = JID("user", "domain", "resource")

    def test_parse(self):
        jid = JID.parse("bob@work/mobile")
        self.assertEqual(str(jid), "bob@work/mobile")

    def test_str(self):
        self.assertEqual(str(self.jid), "user@domain/resource")

    def test_domainid(self):
        self.assertEqual(self.jid.domainid(), "domain")

    def test_nodeid(self):
        self.assertEqual(self.jid.nodeid(), "user@domain")

    def test_ressourceid(self):
        self.assertEqual(self.jid.ressourceid(), "user@domain/resource")

    def test_hashed(self):
        self.assertEqual(self.jid.hashed, "4b8b6b2035fefaeae824f59bd54ebaf763cd61ce")

if __name__ == '__main__':
    unittest.main()
