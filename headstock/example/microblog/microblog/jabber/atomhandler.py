# -*- coding: utf-8 -*-
import feedparser

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

__all__ = ['FeedReaderComponent']

class FeedReaderComponent(component):
    Inboxes = {"inbox"      : "",
               "control"    : ""}
    
    Outboxes = {"outbox"  : "",
                "signal"  : "Shutdown signal"}

    def __init__(self, use_etags=True):
        super(FeedReaderComponent, self).__init__()
        self.last = None
        self.use_etags = use_etags

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                url = self.recv("inbox")
                if self.use_etags and self.last and self.last.etag:
                    d = feedparser.parse(url, etag=self.last.etag)
                else:
                    d = feedparser.parse(url)
                
                if d:
                    self.last = d
                    if d.bozo == 0 and getattr(d, 'status', 200) != 304:
                        self.send(d, "outbox")

            if not self.anyReady():
                self.pause()
  
            yield 1

if __name__ == '__main__':
    from Kamaelia.Chassis.Pipeline import Pipeline
    from Kamaelia.Util.Console import ConsoleEchoer, ConsoleReader

    Pipeline(ConsoleReader("URL: ", ""), 
             FeedReaderComponent(),
             ConsoleEchoer()).run()
