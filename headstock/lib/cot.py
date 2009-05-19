# -*- coding: utf-8 -*-
import re
import time

from bridge import Element as E
from bridge import Document as D
from bridge.common import XMPP_CLIENT_NS
from bridge.filter import lookup

command_regex = re.compile(r"^(.+)\((.*)\):|^(.+):")

__all__ = ['CotScript', 'CotManager', 'CotTest']

class CotTest(object):
    def __init__(self, name):
        self.name = name
        self.running = False
        self.completed = False
        self.stanzas = []
        self.expected_stanzas = []

        self.start = self.end = None
        self.matched = False

    def initiate(self):
        self.running = True
        self.start = time.time()

    def run(self):
        for stanza in self.stanzas:
            yield stanza
        self.completed = True

    def complete(self):
        self.end = time.time()
        self.running = False
    
    def validate(self, stanza):
        for expected_stanza in self.expected_stanzas:
            self.matched = self.match_expected_stanza(stanza, expected_stanza)
            if self.matched:
                self.expected_stanzas.remove(expected_stanza)
                break

    def match_expected_stanza(self, stanza, exp_stanza):
        doc = D()
        doc.xml_children.append(stanza)
        def recurse_children(parent):
            for child in parent.xml_children:
                if isinstance(child, E):
                    for path in get_element_paths(child):
                        match = lookup(doc, path)
                        #print path, type(match)
                        if not match:
                            raise CotMatchError()
                    recurse_children(child)

        try:
            recurse_children(exp_stanza)
        except CotMatchError:
            return False

        return True
        

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
        self.cots = []
        self.current = None
        self.exhausted = False
        self.completed = False
        
    def add(self, cot):
        self.cots.append(cot)

    def run(self):
        for cot in self.cots:
            for test in cot.next_test():
                if self.current:
                    self.current.complete()
                self.current = test
                self.current.initiate()
                for stanza in self.current.run():
                    yield stanza
                    
        if self.current and self.current.running:
            self.current.complete()
        
        self.exhausted = True
        
    def ack_stanza(self, stanza):
        self.current.validate(stanza)

        if self.exhausted and self.current.completed:
            self.completed = True

    def report(self):
        print
        for cot in self.cots:
            for test in cot.next_test():
                if test.matched:
                    print "%s: succeeded in %.3fs" % (test.name, (test.end - test.start))
                else:
                    print "%s: failed in %.3fs" % (test.name,(test.end - test.start))

                print "Remaining expected stanzas that weren't used in matching:"
                for stanza in test.expected_stanzas:
                    print stanza.xml(omit_declaration=True, indent=True)

                print
        print

SEND_MODE = 0
EXPECT_MODE = 1

class CotScript(object):
    def __init__(self):
        self.tests = []

    def next_test(self):
        for test in self.tests:
            yield test

    def load(self, path):
        script = file(path, 'r')
        
        tests = []
        current = None
        mode = SEND_MODE
        
        inside_command = False
        buf = []
        
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
                    if current and mode == EXPECT_MODE:
                        tests.append(current)
                    current = CotTest(name=result[1])
                    mode = SEND_MODE
                elif command == 'expect':
                    mode = EXPECT_MODE
                inside_command = True
            elif line.endswith('}'):
                inside_command = False
                xml = u'<root xmlns="%s">' % XMPP_CLIENT_NS
                xml += ''.join(buf)
                xml += u'</root>'
                root = E.load(xml).xml_root
                
                for child in root.xml_children:
                    child.xml_parent = None
                    if mode == SEND_MODE:
                        current.stanzas.append(child)
                    elif mode == EXPECT_MODE:
                        current.expected_stanzas.append(child)

                buf = []
            else:
                buf.append(line)

        if current:
            tests.append(current)
            
        script.close()

        self.tests = tests
        print tests
        return self
                    
if __name__ == '__main__':
    import sys, pprint
    pprint.pprint(CotScript().load(sys.argv[1]))
