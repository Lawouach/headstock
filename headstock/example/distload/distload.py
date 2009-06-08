# -*- coding: utf-8 -*-
import ConfigParser
from collections import namedtuple
from datetime import datetime
import logging
from logging import handlers
import os, os.path
from multiprocessing import Process, cpu_count

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

class JobClient(object):
    def __init__(self, options, stdout_log=False, log_path=None):
        from headstock.client import Client
        self.client = Client(unicode(options.username), 
                             unicode(options.password), 
                             unicode(options.domain),
                             unicode(options.resource),
                             hostname=options.hostname, 
                             port=int(options.port),
                             usetls=options.tls, 
                             log_file_path=log_path,
                             log_to_console=stdout_log)

    def start(self):
        self.client.activate()

    def stop(self):
        pass

    def add_extensions(self, options):
        from headstock.lib.cot import CotManager
        manager = CotManager()
        manager.add_cot_script(options.cot_file_path)
        
        mapping = []
        from bridge.common import XMPP_ROSTER_NS, XMPP_LAST_NS, XMPP_VERSION_NS
        mapping.append(('query', XMPP_ROSTER_NS))
        mapping.append(('query', XMPP_LAST_NS))
        mapping.append(('query', XMPP_VERSION_NS))
        
        from headstock.client.cot import make_linkages
        components, linkages = make_linkages(mapping, manager)
        self.client.registerComponents(components, linkages)

        from headstock.lib.monitor import make_linkages
        components, linkages = make_linkages(3.0)
        self.client.registerComponents(components, linkages)

    def report(self):
        cot_component = self.client.get_component('cothandler')
        cot_component.manager.report()

XMPPClientOption = namedtuple("XMPPClientOption", "username password domain resource hostname port tls")

class LoadRunnerProcess(Process):
    def __init__(self, job):
        Process.__init__(self, name=job.name)
        self.job = job
        self.clients = []

    def run(self):
        from headstock.lib.utils import generate_unique

        j = self.job
        for i in range(0, j.nb_clients):
            resource = j.resource
            if j.random_resource:
                resource = generate_unique()
            o = XMPPClientOption("%s%d" % (j.username_prefix, j.username_suffix_offset + i), 
                                 j.password, j.domain, resource, j.hostname, j.port, j.tls)
            log_path = None
            if j.log_dir:
                log_path = '%s.log' % os.path.join(j.log_dir, o.username)
            c = JobClient(o, j.log_to_stdout, log_path)
            c.add_extensions(j)
            self.clients.append(c)
            c.start()

        from Axon.Scheduler import scheduler 
        scheduler.immortalise()
        scheduler.run.runThreads()

        for c in self.clients:
            c.report()

class XMPPDistributedLoadManager(object):
    def __init__(self, config):
        self.config = Config.from_ini(config)

    def open_logger(self, log_base_dir):
        self.logger = logger = logging.getLogger("distload.main.logger")
        logger.setLevel(logging.INFO)

        log_base_dir = os.path.abspath(log_base_dir)
        if not os.path.exists(log_base_dir):
            os.makedirs(log_base_dir)

        path = os.path.join(log_base_dir, "distload.log")
        h = handlers.RotatingFileHandler(path, maxBytes=1048576, backupCount=5)
        h.setLevel(logging.INFO)
        h.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
        logger.addHandler(h)

    def close_logger(self):
        for handler in self.logger.handlers:
            handler.flush()
            handler.close()
        self.logger = None

    def log(self, msg, level=logging.INFO):
        if self.logger:
            self.logger.log(level, msg)

    def run(self):
        self.open_logger(self.config.run.log_dir)

        start_time = datetime.utcnow()
        self.log("Starting run: %s" % start_time.isoformat())
        self.log("CPU count: %d" % cpu_count())
        self.log("Pool size: %d" % self.config.run.pool_size)

        for i in range(0, min(self.config.run.pool_size, self.config.run.jobs)):
            job = self.config.get_section_by_suffix('job', str(i))
            if job:
                self.log("Adding job: %s" % job.name)
                LoadRunnerProcess(job).run() #start()

        end_time = datetime.utcnow()
        self.log("Finishing run: %s" % end_time.isoformat())
        diff = end_time - start_time
        self.log("Run lasted: %d days %d seconds %d microseconds" % (diff.days, diff.seconds, diff.microseconds))
        
        self.close_logger()

if __name__ == '__main__':
    def parse_commandline():
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config",
                          help="Configuration file")
        (options, args) = parser.parse_args()

        return options

    options = parse_commandline()
    XMPPDistributedLoadManager(options.config).run()
