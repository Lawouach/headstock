# -*- coding: utf-8 -*-
import itertools
import re
import time

from bridge import Element as E
from bridge import Document as D
from bridge.common import XMPP_CLIENT_NS
from bridge.filter import lookup

command_regex = re.compile(r"^(.+)\((.*)\):|^(.+):")

__all__ = ['CotScript', 'CotManager', 'Cot']

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
        self._stanzas = []

    @property
    def stanzas(self):
        for stanza in self._stanzas:
            yield stanza
            
    def add_cot_script(self, cot_script):
        stanzas = CotScript.load(cot_script)
        self._stanzas = itertools.chain(self._stanzas, stanzas)

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
                    stanzas.append({SEND_MODE: {}, EXPECT_MODE: {}})
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
                    stanza_id = child.get_attribute_value('id')
                    stanza_type = child.get_attribute_value('type')
                    stanzas[-1][mode][(stanza_id, stanza_type)] = (current_test_name, child)

                buf = []
            else:
                buf.append(line)

        script.close()
        return stanzas

class Cot(object):
    def __init__(self, bus, scripts, timeout=5.0):
        self.bus = bus
        self.client = None
        self.timeout = timeout
        self.manager = CotManager()

        for cot in scripts:
            self.manager.add_cot_script(cot)

        self.stanzas = self.manager.stanzas
        self.current = None
        self.sendable = None
        self.keys = []

        self._last = 0
        self.results = []

        self.processing = False

        self.current_test_name = None
        
    def ready(self, client):
        self.client = client
        self.bus.subscribe("main", self._process)

    def stopping(self):
        self.bus.unsubscribe("main", self._process)

    def cleanup(self):
        pass

    def terminated(self):
        import pprint
        pprint.pprint(self.results)

    @property
    def hostname(self):
        if self.client:
            return self.client.jid.domain

    def _process(self):
        try:
            if self.processing:
                now = time.time()
                if now > self._last + self.timeout:
                    self.results.append(('fail', self.current_test_name,
                                         now - self._last))
                    self._last = 0
                    self.current = None
                    self.sendable = None
                    self.processing = False
                    self.current_test_name = None

            if not self.processing and not self.sendable:
                try:
                    self.current = self.stanzas.next()
                except StopIteration:
                    self.bus.unsubscribe("main", self._process)
                    return
                self.sendable = self.current[SEND_MODE].iterkeys()

            if not self.processing:
                try:
                    self._next()
                except StopIteration:
                    return
        except Exception, ex:
            self.bus.log(traceback=True)
                
    def _next(self):
        self._last = 0
        self.processing = True
        
        stanza_id, stanza_type = self.sendable.next()
        
        self.current_test_name, stanza = self.current[SEND_MODE][(stanza_id, stanza_type)]
        stanza = stanza.xml(omit_declaration=True).replace("$(hostname)",
                                                           self.hostname)
        e = E.load(stanza).xml_root

        for stanza_id, stanza_type in self.current[EXPECT_MODE]:
            self.keys.append((stanza_id, stanza_type))
            self.client.register_on_iq(self._handle_response,
                                       id=stanza_id, type=stanza_type,
                                       once=True)
        self._last = time.time()
        self.client.send_stanza(e)
            
    def _handle_response(self, e):
        now = time.time()
        try:
            stanza_id = e.get_attribute_value('id')
            stanza_type = e.get_attribute_value('type')

            key = (stanza_id, stanza_type)

            if key in self.current[EXPECT_MODE]:
                del self.current[EXPECT_MODE][key]
            elif (None, stanza_type) in self.current[EXPECT_MODE]:
                del self.current[EXPECT_MODE][(None, stanza_type)]

            if not self.current[EXPECT_MODE]:
                self.results.append(('success', self.current_test_name, now - self._last))
                for key in self.keys:
                    try:
                        self.client.unregister_from_iq(self._handle_response,
                                                       id=stanza_id, type=stanza_type,
                                                       once=True)
                    except:
                        pass
                self.keys = []
                self._last = 0
                self.processing = False
                self.sendable = None
                self.current_test_name = None
        except Exception, ex:
            self.bus.log(traceback=True)

            
if __name__ == '__main__':
    import sys, pprint
    pprint.pprint(CotScript().load(sys.argv[1]))

    manager = CotManager()
    manager.add_cot_script(sys.argv[1])

    for s in manager.stanzas:
        print s.xml()

    print manager.report()
