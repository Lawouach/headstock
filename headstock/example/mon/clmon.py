# -*- coding: utf-8 -*-
import os, os.path
import ConfigParser
import time
import logging
from logging import handlers
import threading
import signal
from collections import namedtuple
from multiprocessing import Process, active_children
from multiprocessing.connection import Listener, Client

from memcache import Client as MemcachedClient
from cherrypy.process import plugins

import clext

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

    def __contains__(self, key):
        return key in self.__dict__

    def get_section_by_suffix(self, prefix, suffix, default=None):
        key = "%s%s" % (prefix, suffix)
        return getattr(self, key, default)

CONNECTING = 0
CONNECTED = 1
DISCONNECTED = 2

PENDING = 0
SUCCESS = 1
FAILURE = 2

class XMPPWatchdogClient(object):
    def __init__(self, options, memcache_addr):
        self.conn = None
        self.running = False

        self.status = CONNECTING
        self._statuses = {}

        self.options = options
        self.mc = MemcachedClient(memcache_addr)
        self.init_client()

    def init_client(self):
        from headstock.client import Client
        class _Client(Client):
            def active(self):
                self.watchdog.status = CONNECTED

            def terminated(self):
                self.watchdog.status = DISCONNECTED
                #scheduler.run.stop()

        options = self.options
        self.client = _Client(username=unicode(options.username),
                              password=unicode(options.password),
                              domain=unicode(options.domain),
                              resource=unicode(options.resource),
                              hostname=unicode(options.hostname),
                              port=int(options.port),
                              usetls=False,
                              register=False,
                              unregister=False,
                              log_file_path=os.path.join(options.log_dir,
                                                         'xmpp.%s.log' % options.username),
                              log_to_console=options.log_to_stdout)
        self.client.watchdog = self
        self.add_extensions()

    def start(self):
        self.running = True
        self.conn = Client(('localhost', 12001), authkey='supervisor')
        self.conn.send(str(os.getpid()))
        self.client.activate()
        
    def stop(self):
        self.client.shutdown()
        self.running = False
        if self.conn:
            self.conn.close()
            self.conn = None

    def add_extensions(self):
        from headstock.client.presence import make_linkages
        components, linkages = make_linkages(presence_handler_cls=clext.PresenceHandler)
        self.client.registerComponents(components, linkages)

        from headstock.client.roster import make_linkages
        components, linkages = make_linkages(roster_handler_cls=clext.RosterHandler)
        self.client.registerComponents(components, linkages)

        from headstock.client.im import make_linkages
        components, linkages = make_linkages(im_handler_cls=clext.MessagePingPong)
        self.client.registerComponents(components, linkages)

        presence_component = self.client.get_component('presencehandler')
        presence_component.watchdog = self

        im_component = self.client.get_component('msghandler')
        im_component.watchdog = self

        roster_handler = self.client.get_component('rosterhandler')
        roster_handler.watchdog = self

        if self.options.type == 'ping':
            im_component.marker = str(self.options.im_marker)
            presence_component.marker = str(self.options.presence_marker)

            roster_handler.handlers.append(im_component)
            roster_handler.handlers.append(presence_component)

            for node in self.options.nodes.split(','):
                node = str(node).strip()
                self._statuses[node] = {}
                for marker in self.options.markers.split(','):
                    self._statuses[node][str(marker).strip()] = PENDING

    def store(self, marker, value):
        self.mc.set(marker, str(value))

    def fail(self, node):
        markers = self.options.markers.split(',')
        if self.options.im_marker in markers:
            marker = '%s_%s' % (str(self.options.im_marker), node)
            self.store(marker, 100000)
        
        if self.options.presence_marker in markers:
            marker = '%s_AVAILABLE_%s' % (str(self.options.presence_marker), node)
            self.store(marker, 100000)
            marker = '%s_UNAVAILABLE_%s' % (str(self.options.presence_marker), node)
            self.store(marker, 100000)

    def failed(self, node, marker):
        self._statuses[node][marker] = FAILED

    def succeeded(self, node, marker):
        self._statuses[node][marker] = SUCCESS

        can_stop = True
        for marker in self._statuses[node]:
            if self._statuses[node][marker] == PENDING:
                can_stop = False
                break
            
        if can_stop:
            self.stop()

    def check_statuses(self):
        if self.status == CONNECTING:
            # houston we couldn't connect
            node = str(self.options.resource)
            self.fail(node)
            yield node

        for node in self._statuses:
            for marker in self._statuses[node]:
                if self._statuses[node][marker] != SUCCESS:
                    self.fail(node)
                    yield node
                    break

class WatchdogPlugin(plugins.SimplePlugin):
    def __init__(self, bus, options, memcached_addr):
        self.bus = bus
        self.options = options
        self.client = None
        self.memcached_addr = memcached_addr

    def start(self):
        self.bus.log("Starting Watchdog client")

        from Axon.Scheduler import scheduler 
        scheduler.immortalise()

        from headstock.lib.monitor import ThreadedMonitor
        class _ThreadedMonitor(ThreadedMonitor):
            def __init__(self, watchdog, freq):
                super(_ThreadedMonitor, self).__init__(freq)
                self.watchdog = watchdog

            def timeout(self):
                if self.watchdog.options.type == 'ping':
                    self.watchdog.check()
                self.watchdog.restart_client()
                self.reset(self.interval)

            def terminate(self):
                self.reset(0)

        self.monitor = _ThreadedMonitor(self, self.options.monitor_timeout)
        self.monitor.activate()

        self.client = XMPPWatchdogClient(self.options, self.memcached_addr)
        self.client.start()

    def stop(self):
        self.bus.log("Stopping Watchdog client")
        self.monitor.terminate()
        if self.client:
            self.client.stop()
            self.client = None

    def check(self):
        for failing_node in self.client.check_statuses():
            self.bus.log("Node failure: %s" % failing_node)

    def restart_client(self):
        self.bus.log("Restarting Watchdog client")
        self.client.stop()
        self.client = XMPPWatchdogClient(self.options, self.memcached_addr)
        self.client.start()

class Watchdog(Process):
    def __init__(self, options, memcached_addr):
        Process.__init__(self)
        self.logger = None
        self.options = options
        self.memcached_addr = memcached_addr

    def run(self):
        base_log_dir = os.path.join(os.getcwd(), 'logs')
        self.logger = open_logger(base_log_dir, "watchdog.%s.log" % self.options.username, "watchdog.logger")

        from cherrypy.process.wspbus import Bus
        self.bus = bus = Bus()
        bus.subscribe('log', self.log)

        self.log("Watchdog PID: %d" % self.pid)

        from cherrypy.process import plugins  
        plugins.SignalHandler(bus).subscribe()

        WatchdogPlugin(bus, self.options, self.memcached_addr).subscribe()
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

if __name__ == '__main__':
    def parse_commandline():
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config",
                          help="Configuration file")
        (options, args) = parser.parse_args()

        return options
    options = parse_commandline()

    from conductor.supervisor import SupervisorTask
    class WatchdogSupervisorTask(SupervisorTask):
        def start_task(self):
            for i in range(0, self.config.run.watchdogs):
                options = self.config.get_section_by_suffix('watchdog', str(i))
                w = Watchdog(options, memcached_addr)
                self.watchdogs.append(w)
                w.start()
                time.sleep(0.1)

    from conductor.supervisor import Supervisor
    s = Supervisor(os.getcwd(), options.config)
    t = WatchdogSupervisorTask()
    s.register_task(t)
    s.run()
