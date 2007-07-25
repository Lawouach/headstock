# -*- coding: utf-8 -*-

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished

import logging

class Logger(component):
    Inboxes = {"inbox" : "String to be logged",
               "control" : "Closes the logger",}
    Outboxes = {"outbox" : "UNUSED",
                "signal" : "UNUSED",}
   
    def __init__(self, path, stdout=False):
        super(Logger, self).__init__()

        self.path = path
        self.with_stdout = stdout

    def main(self):
        logger = logging.getLogger("kamaelia.logger")
        logger.setLevel(logging.DEBUG)
        
        logfmt = logging.Formatter("[%(asctime)s] %(message)s")

        if self.path:
            h = logging.FileHandler(self.path)
            h.setLevel(logging.DEBUG)
            h.setFormatter(logfmt)
            logger.addHandler(h)

        if self.with_stdout:
            import sys
            h = logging.StreamHandler(sys.stdout)
            h.setLevel(logging.DEBUG)
            h.setFormatter(logfmt)
            logger.addHandler(h)

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or isinstance(mes, producerFinished):
                    logger.close()
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                msg = self.recv("inbox")
                logger.debug(msg)

            if not self.anyReady():
                self.pause()
  
            yield 1
            
        
