#!/usr/bin/env python

import unittest
from headstock.lib.stanza import Stanza

class TestStanza(unittest.TestCase):
    
    def test_to_element(self):
        stanza = Stanza(name="iq", from_jid="bob", to_jid="alice", type="get", stanza_id="i")
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<iq xmlns="jabber:client" to="alice" type="get" id="i" from="bob" />'
        self.assertEqual(Stanza.to_element(stanza).xml(), xml)
        stanza.swap_jids()
        xml_swapped = '<?xml version="1.0" encoding="UTF-8"?>\n<iq xmlns="jabber:client" to="bob" type="get" id="i" from="alice" />'
        self.assertEqual(Stanza.to_element(stanza).xml(), xml_swapped)

    def test_get_iq(self):
        stanza = Stanza.get_iq(from_jid="bob", to_jid="alice", stanza_id="i")
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<iq xmlns="jabber:client" to="alice" type="get" id="i" from="bob" />'
        self.assertEqual(stanza.xml(), xml)
    
    def test_set_iq(self):
        stanza = Stanza.set_iq(from_jid="bob", to_jid="alice", stanza_id="i")
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<iq xmlns="jabber:client" to="alice" type="set" id="i" from="bob" />'
        self.assertEqual(stanza.xml(), xml)

    def test_result_iq(self):
        stanza = Stanza.result_iq(from_jid="bob", to_jid="alice", stanza_id="i")
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<iq xmlns="jabber:client" to="alice" type="result" id="i" from="bob" />'
        self.assertEqual(stanza.xml(), xml)
        
    def test_error_iq(self):
        stanza = Stanza.error_iq(from_jid="bob", to_jid="alice", stanza_id="i")
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<iq xmlns="jabber:client" to="alice" type="error" id="i" from="bob" />'
        self.assertEqual(stanza.xml(), xml)

    def test_uniq_id(self):
        xml1 = Stanza.get_iq().xml()
        xml2 = Stanza.get_iq().xml()
        self.assertNotEqual(xml1, xml2)

if __name__ == '__main__':
    unittest.main()
