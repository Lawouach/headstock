# -*- coding: utf-8 -*-
import os, os.path
import logging
from logging import handlers
import traceback as _traceback
from sys import exc_info as _exc_info

__all_ = ['Logger']

class Logger(object):
    def __init__(self, path=None, stdout=False, name=None):
        self.path = path
        self.with_stdout = stdout
        self.name = name

        logger = logging.getLogger("headstock.logger.%s" % self.name or '')
        logger.setLevel(logging.DEBUG)
        
        logfmt = logging.Formatter("[%(asctime)s] %(message)s")

        file_handler = None
        stdout_handler = None

        if self.path:
            h = handlers.RotatingFileHandler(self.path, maxBytes=10485760, backupCount=3)
            h.setLevel(logging.DEBUG)
            h.setFormatter(logfmt)
            logger.addHandler(h)

        if self.with_stdout:
            import sys
            h = logging.StreamHandler(sys.stdout)
            h.setLevel(logging.DEBUG)
            h.setFormatter(logfmt)
            logger.addHandler(h)

        self.logger = logger

    def log(self, m, traceback=False):
        self.logger.debug(m)

    def error(self):
        exc = _exc_info()
        self.logger.error("".join(_traceback.format_exception(*exc)))

    def close(self):
        for handler in self.logger.handlers:
            handler.close()
            logger.removeHandler(handler)
