# -*- coding: utf-8 -*-

# see http://trac.defuze.org/wiki/bridge
from bridge.parser import DispatchParser

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

from xml.sax import SAXParseException

__all__ = ['XMLIncrParser']

class XMLIncrParser(component):
    Inboxes = {"inbox" : "Byte string chunk to feed the XML parser",
               "control" : "Stop the parsing.",
               "reset": "Reset the parser state"}
    Outboxes = {"outbox" : "When an element parsing is completed, it is placed there as a bridge.Element instance.",
                "signal" : "Shutdown signal",}
   
    def __init__(self):
        super(XMLIncrParser, self).__init__()

    def _done(self, e):
        # ``e`` is a bridge.Element instance 
        self.send(e, "outbox")
        #print e.xml(omit_declaration=True)
        
    def main(self):
        p = DispatchParser()
        # The DispatchParser allows to register callbacks per local name
        # and namespaces. But here we simply register a default callback
        # for any XML element parsed successfully and drop it into the outbox
        # so that components that will be linked to it will have to make
        # the decision whether or not the element is relevant to them
        # or simply discard it.
        p.register_default(self._done)
        yield 1
        
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("reset"):
                command = self.recv("reset")
                if command == "RESET":
                    p.reset()

            if self.dataReady("inbox"):
                data = self.recv("inbox")
                try:
                    p.feed(data)
                except SAXParseException:
                    self.send(producerFinished(), "signal")

            if not self.anyReady():
                self.pause()
  
            yield 1
