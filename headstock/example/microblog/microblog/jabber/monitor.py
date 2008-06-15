# -*- coding: utf-8 -*-
from Axon.AdaptiveCommsComponent import AdaptiveCommsComponent
from Axon.Ipc import shutdownMicroprocess, producerFinished
from Kamaelia.Util.Clock import CheapAndCheerfulClock  

__all__ = ['HTTPResourceMonitor']

class HTTPResourceMonitor(AdaptiveCommsComponent):
    Inboxes = {"inbox"      : "",
               "control"    : "",
               "monitor"    : "",}
    
    Outboxes = {"outbox"  : "",
                "signal"  : "Shutdown signal"}

    def __init__(self, freq=1.0):
        super(HTTPResourceMonitor, self).__init__()
        self.urls = []
        self.freq = freq

    def initComponents(self):
        self.clock = CheapAndCheerfulClock(self.freq)
        self.link((self.clock, 'outbox'), (self, 'inbox'))
        self.addChildren(self.clock)
        self.clock.activate()

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("monitor"):
                url, comp = self.recv("monitor")
                comp.activate()
                newOut = self.addOutbox("monitoredOut")
                self.link((self, newOut), (comp, 'inbox'))
                self.addChildren(comp)
                self.urls.append((url, newOut))
                
            if self.dataReady("inbox"):
                self.recv("inbox")
                for url, targetOutbox in self.urls:
                    self.send(url, targetOutbox)

            if not self.anyReady():
                self.pause()
  
            yield 1

if __name__ == '__main__':
    from Kamaelia.Util.Console import ConsoleEchoer
    from Kamaelia.Util.OneShot import OneShot
    from atomhandler import FeedReaderComponent

    shot = OneShot()

    monitor = HTTPResourceMonitor()
    monitor.link((shot, 'outbox'), (monitor, 'monitor'))

    feedreader = FeedReaderComponent()
    printer = ConsoleEchoer()
    feedreader.link((feedreader, 'outbox'), (printer, 'inbox'))
    
    shot.send(('http://localhost:8080/profile/feed', feedreader))

    printer.activate()
    feedreader.activate()
    #shot.activate()
    monitor.run()

    
