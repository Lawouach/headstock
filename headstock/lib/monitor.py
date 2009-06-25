# -*- coding: utf-8 -*-
import time

from Axon.ThreadedComponent import threadedcomponent
from Axon.Ipc import shutdownMicroprocess, producerFinished

from Kamaelia.Util.OneShot import OneShot

__all__ = ['ThreadedMonitor', 'make_linkages']

class ThreadedMonitor(threadedcomponent):
    def __init__(self, interval):
        super(ThreadedMonitor, self).__init__()
        self.interval = interval

    def main(self):
        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady('inbox'):
                self.interval = self.recv('inbox')

            if self.interval > 0:
                time.sleep(self.interval)
                self.timeout()
            else:
                break
            
            if not self.anyReady():
                self.pause()

    def timeout(self):
        self.send(True, "outbox")

    def reset(self, freq): 
        o = OneShot(msg=freq)
        o.link((o, 'outbox'), (self, 'inbox'))
        o.activate()

def make_linkages(freq):
    linkages = {("monitor", "outbox"): ('client', "ping"),
                ("client", "_stopmonitor"): ("monitor", "control")}
    return dict(monitor=ThreadedMonitor(freq)), linkages
    
