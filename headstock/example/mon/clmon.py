# -*- coding: utf-8 -*-
import os, os.path
import ConfigParser
import time
import logging
from logging import handlers
import threading
from collections import namedtuple
from multiprocessing import Process, active_children
from multiprocessing.connection import Listener, Client

from cherrypy.process import plugins

import signal
try:
    from os import kill
    from signal import SIGTERM
    def kill_proc(pid): kill(pid, SIGTERM)
except ImportError:
    SIGTERM = None
    # http://www.python.org/doc/faq/windows/#how-do-i-emulate-os-kill-in-windows
    def kill_proc(pid):
        """kill function for Win32"""
        import win32api
        handle = win32api.OpenProcess(1, 0, pid)
        return (0 != win32api.TerminateProcess(handle, 0))


def open_logger(log_base_dir, log_filename, logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    log_base_dir = os.path.abspath(log_base_dir)
    if not os.path.exists(log_base_dir):
        os.makedirs(log_base_dir)
        
    path = os.path.join(log_base_dir, log_filename)
    h = handlers.RotatingFileHandler(path, maxBytes=1048576, backupCount=5)
    h.setLevel(logging.INFO)
    h.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
    logger.addHandler(h)

    return logger
               
def close_logger(logger_name):
    logger = logging.getLogger(logger_name)
    for handler in logger.handlers:
        handler.flush()
        handler.close()

class Config(object):
    @staticmethod
    def from_ini(filepath, encoding='ISO-8859-1'):
        config = ConfigParser.ConfigParser()
        config.readfp(file(filepath, 'rb'))

        conf = Config()
        for section in config.sections():
            section_prop = Config()
            section_prop.keys = []
            setattr(conf, section, section_prop)
            for option in config.options(section):
                section_prop.keys.append(option)
                value = Config._convert_type(config.get(section, option).decode(encoding))
                setattr(section_prop, option, value)

        return conf

    @staticmethod
    def _convert_type(value):
        """Do dummy conversion of the string 'True', 'False' and 'None'
        into their object equivalent"""
        if value == 'True':
            return True
        elif value == 'False':
            return False
        elif value == 'None':
            return None
        try:
            return int(value)
        except:
            pass
        return value

    def get(self, section, option, default=None, raise_error=False):
        if hasattr(self, section):
            obj = getattr(self, section, None)
            if obj and hasattr(obj, option):
                return getattr(obj, option, default)

        if raise_error:
            raise AttributeError("%s %s" % (section, option))

        return default

    def get_section_by_suffix(self, prefix, suffix, default=None):
        key = "%s%s" % (prefix, suffix)
        return getattr(self, key, default)

class XMPPWatchdogClient(object):
    def __init__(self, options):
        self.conn = None

        from Axon.Scheduler import scheduler 
        scheduler.immortalise()

        from headstock.client import Client
        class _Client(Client):
            def terminated(self):
                scheduler.run.stop()

        self.client = _Client(username=unicode(options.username),
                              password=unicode(options.password),
                              domain=unicode(options.domain),
                              resource=unicode(options.resource),
                              hostname=unicode(options.hostname),
                              port=int(options.port),
                              usetls=False,
                              register=False,
                              unregister=False,
                              log_file_path=os.path.join(options.log_dir, 'xmpp.%s.log' % options.username),
                              log_to_console=options.log_to_stdout)
        self.add_extensions()

    def start(self):
        self.conn = Client(('localhost', 12001), authkey='supervisor')
        self.conn.send(str(os.getpid()))
        self.client.activate()
        
    def stop(self):
        self.client.shutdown()
        if self.conn:
            self.conn.close()
            self.conn = None

    def add_extensions(self):
        from headstock.client.presence import make_linkages
        components, linkages = make_linkages()
        self.client.registerComponents(components, linkages)

        from headstock.client.roster import make_linkages
        components, linkages = make_linkages()
        self.client.registerComponents(components, linkages)

        from headstock.client.im import make_linkages
        components, linkages = make_linkages()
        self.client.registerComponents(components, linkages)
    
class WatchdogPlugin(plugins.SimplePlugin):
    def __init__(self, bus, options):
        self.bus = bus
        self.client = XMPPWatchdogClient(options)

    def start(self):
        self.bus.log("Starting Watchdog client")
        self.client.start()

    def stop(self):
        self.bus.log("Stopping Watchdog client")
        self.client.stop()

class Watchdog(Process):
    def __init__(self, options):
        Process.__init__(self)
        self.logger = None
        self.options = options

    def run(self):
        base_log_dir = os.path.join(os.getcwd(), 'logs')
        self.logger = open_logger(base_log_dir, "watchdog.proc.log", "watchdog.logger")

        from cherrypy.process.wspbus import Bus
        self.bus = bus = Bus()
        bus.subscribe('log', self.log)

        self.log("Watchdog PID: %d" % self.pid)

        from cherrypy.process import plugins  
        plugins.SignalHandler(bus).subscribe()

        WatchdogPlugin(bus, self.options).subscribe()
        bus.start()

        try:
            from Axon.Scheduler import scheduler 
            scheduler.run.runThreads(slowmo = 0.02)
        except KeyboardInterrupt:
            bus.exit()

        close_logger("watchdog.logger")

    def log(self, msg, level=logging.INFO):
        if self.logger:
            self.logger.log(level, msg)

class WatchdogListener(threading.Thread):
    def __init__(self, bus):
        threading.Thread.__init__(self)
        self.running = False
        self.connections = []
        self.bus = bus
        self.listener = Listener(('localhost', 12001), authkey="supervisor")
        
    def run(self):
        self.bus.log("Listening for incoming connections")
        self.running = True
        while self.running:
            conn = self.listener.accept()
            pid = conn.recv()
            self.bus.log("Listening from process: %s" % pid)
            self.connections.append((pid, conn))

    def stop(self):
        self.bus.log("Stopping listener")
        self.running = False
        for pid, conn in self.connections:
            if conn:
                conn.close()
        # Workaround:
        # There seems to be a bug in teh Listener 
        # which doesn't unblock on accept when it is closed
        # We connect and disconnect so that we escape the accept() call
        c = Client(('localhost', 12001), authkey='supervisor')
        c.send(str(os.getcwd()))
        c.close()
        self.connections = []
        self.listener.close()

class WatchdogSupervisorPlugin(plugins.SimplePlugin):
    def __init__(self, bus, config):
        self.bus = bus
        self.config = config
        self.listener = WatchdogListener(bus)
        self.watchdogs = []

    def start(self):
        self.bus.log("Starting Watchdog")
        self.listener.start()

        from headstock.lib.utils import generate_unique
        
        for i in range(0, self.config.run.watchdogs):
            options = self.config.get_section_by_suffix('watchdog', str(i))
            resource = unicode(options.resource)
            if options.random_resource:
                resource = generate_unique()
            w = Watchdog(options)
            self.watchdogs.append(w)
            w.start()

    def stop(self):
        self.bus.log("Stopping Watchdogs")
        self._kill_watchdog()
        if self.listener:
            self.listener.stop()
            self.listener.join()
            self.listener = None

    def exit(self):
        self.bus.log("Exiting Watchdogs")
        self.stop()

    def _kill_watchdog(self):
        for watchdog in self.watchdogs:
            if watchdog.is_alive():
                kill_proc(watchdog.pid)
                watchdog.join()
        self.watchdogs = []

class WatchdogSupervisor(object):
    def __init__(self, config_path):
        self.config = Config.from_ini(config_path)

    def run(self):
        base_log_dir = os.path.join(os.getcwd(), 'logs')
        self.logger = open_logger(base_log_dir, "watchdog.supervisor.log", "watchdog.supervisor.logger")

        from cherrypy.process.wspbus import Bus
        self.bus = bus = Bus()
        bus.subscribe('log', self.log)

        self.log("Starting Watchdog supervisor")

        plugins.SignalHandler(bus).subscribe()

        WatchdogSupervisorPlugin(bus, self.config).subscribe()
        bus.start()
        bus.block()
        
        close_logger("watchdog.supervisor.logger")
    
    def log(self, msg, level=logging.INFO):
        if self.logger:
            self.logger.log(level, msg)

if __name__ == '__main__':
    def parse_commandline():
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config",
                          help="Configuration file")
        (options, args) = parser.parse_args()

        return options

    options = parse_commandline()
    w = WatchdogSupervisor(options.config)
    w.run()
    
