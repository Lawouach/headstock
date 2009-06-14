# -*- coding: utf-8 -*-
import itertools
import re
import time

from bridge import Element as E
from bridge import Document as D
from bridge.common import XMPP_CLIENT_NS
from bridge.filter import lookup

command_regex = re.compile(r"^(.+)\((.*)\):|^(.+):")

__all__ = ['CotScript', 'CotManager']

class CotMatchError(BaseException):
    pass

def get_element_paths(element):
    attrs = element.xml_attributes
    path = ''
    while 1:
        if not element.xml_name:
            break
        if not element.xml_ns:
            path = u'/%s' % element.xml_name + path
        else:
            path = u'/{%s}%s' % (element.xml_ns, element.xml_name) + path
        element = element.xml_parent
        if not element:
            break

    yield path
    
    for attr in attrs:
        yield path + '[@%s="%s"]' % (attr.xml_name, attr.xml_text or '')

class CotManager(object):
    def __init__(self):
        self.series = {}
        self.nb_stanzas = 0
        self.current_index = 0
        self._stanzas = []
        self.expected_stanzas = []
        self.exhausted = False
        self.done_validating = False

    @property
    def stanzas(self):
        for test_name, stanza in self._stanzas:
            self.current_index += 1
            yield stanza
            
    @property
    def completed(self):
        return self.exhausted and self.done_validating

    def is_expected(self, stanza):
        return stanza.get_attribute_value('id') in self.series

    def reviewed(self, stanza):
        stanza_id = stanza.get_attribute_value('id')
        return self.series[stanza_id]['reviewed']
        
    def add_cot_script(self, cot_script):
        stanzas, expected_stanzas = CotScript.load(cot_script)
        self.nb_stanzas += len(stanzas)
        self._stanzas = itertools.chain(self._stanzas, stanzas)

        for test_name, stanza in expected_stanzas:
            stanza_id = stanza.get_attribute_value('id')
            self.series[stanza_id] = {'test': test_name, 'matched': False, 'reviewed': False,
                                      'type': stanza.xml_name, 'ns': stanza.xml_ns}
            self.expected_stanzas.append(stanza)

    def validate(self, stanza, filler_cb):
        matched = False
        for s in self.expected_stanzas:
            expected_stanza = s.clone().xml_root

            expected_stanza = filler_cb(expected_stanza)
            matched = self.match_expected_stanza(stanza, expected_stanza)
            if matched:
                stanza_id = expected_stanza.get_attribute_value('id')
                self.series[stanza_id]['matched'] = True
                self.expected_stanzas.remove(s)
                break

    def match_expected_stanza(self, stanza, exp_stanza):
        doc = D()
        doc.xml_children.append(stanza)
        stanza.xml_parent = doc
        def recurse_children(element):
            for path in get_element_paths(element):
                match = lookup(doc, path)
                #print path, type(match)
                if not match:
                    raise CotMatchError()

            for child in element.xml_children:
                if isinstance(child, E):
                    recurse_children(child)

        try:
            recurse_children(exp_stanza)
        except CotMatchError:
            stanza.xml_parent = None
            doc.xml_children = []
            return False

        stanza.xml_parent = None
        doc.xml_children = []
        return True

    def ack_stanza(self, stanza, filler_cb):
        stanza_id = stanza.get_attribute_value('id')
        self.series[stanza_id]['reviewed'] = True
        self.validate(stanza, filler_cb)
        
        if self.exhausted:
            self.done_validating = True

    def report(self):
        print
        for serie in self.series.values():
            if serie['matched']:
                print "%s: succeeded" % (serie['test'],)
            else:
                print "%s: failed" % (serie['test'],)

        if self.expected_stanzas:
            print "Remaining expected stanzas that weren't used in matching:"
            for stanza in self.expected_stanzas:
                print stanza.xml(omit_declaration=True, indent=True)
                
        print

SEND_MODE = 0
EXPECT_MODE = 1

class CotScript(object):
    @staticmethod
    def load(path):
        script = file(path, 'r')
        
        mode = SEND_MODE
        
        inside_command = False
        buf = []

        stanzas = []
        expected_stanzas = []
        current_test_name = None
        
        for line in script:
            line = line.strip()
            if not inside_command:
                if not line:
                    continue
            
                if line.startswith('#'):
                    continue
                
                m = command_regex.match(line)
                if not m:
                    continue
            
                result = m.groups()
                command = result[0] or result[2]
                if command == 'send':
                    current_test_name = result[1]
                    mode = SEND_MODE
                elif command == 'expect':
                    mode = EXPECT_MODE
                inside_command = True
            elif line.endswith('}') and inside_command:
                inside_command = False
                xml = u'<root xmlns="%s">' % XMPP_CLIENT_NS
                xml += ''.join(buf)
                xml += u'</root>'
                root = E.load(xml).xml_root
                
                for child in root.xml_children:
                    child.xml_parent = None
                    if mode == SEND_MODE:
                        stanzas.append((current_test_name, child))
                    elif mode == EXPECT_MODE:
                        expected_stanzas.append((current_test_name, child))

                buf = []
            else:
                buf.append(line)

        script.close()

        return stanzas, expected_stanzas
                    
if __name__ == '__main__':
    import sys, pprint
    pprint.pprint(CotScript().load(sys.argv[1]))
