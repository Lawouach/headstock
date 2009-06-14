# -*- coding: utf-8 -*-
import time

from Axon.ThreadedComponent import threadedcomponent
from Axon.Ipc import shutdownMicroprocess, producerFinished

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
                
            if self.interval > 0:
                time.sleep(self.interval)
            else:
                break

            self.send(True, "outbox")

            while not self.anyReady():
                self.pause()

            if self.dataReady('inbox'):
                self.interval = self.recv('inbox')

def make_linkages(freq):
    linkages = {("monitor", "outbox"): ('client', "ping"),
                ("client", "_stopmonitor"): ("monitor", "control")}
    return dict(monitor=ThreadedMonitor(freq)), linkages
    
