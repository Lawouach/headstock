# -*- coding: utf-8 -*-

from headstock.api.client.threaded import ThreadedBaseClient

from bridge import Element as E
from bridge.parser import DispatchParser

class Demo(ThreadedBaseClient):
    def __init__(self):
        ThreadedBaseClient.__init__(self, 'localhost', 5222)

    def setup(self):
        self.set_jid_details(u'localhost', u'test', u'test') 
        self.set_logger('./test.log', True)
        
        ThreadedBaseClient.setup(self)
        
if __name__ == '__main__':
    demo = Demo()
    try:
        demo.setup()
        demo.start()
    except KeyboardInterrupt:
        demo.stop()
    except Exception, ex:
        print ex
        demo.stop()
        raise
    
