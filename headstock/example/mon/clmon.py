# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import os, os.path
    import time
    base_dir = os.getcwd()
    log_dir = os.path.join(base_dir, 'logs')

    def parse_commandline():
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-c", "--config", dest="config",
                          help="Configuration file")
        parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
                          help="Outputs XMPP clients trace to stdout")
        (options, args) = parser.parse_args()

        return options
    options = parse_commandline()

    from memcache import Client as MemcacheClient

    from conductor.lib.logger import open_logger, close_logger
    from conductor.connection import ProcClient, ProcListener

    from conductor.supervisor import SupervisorTask
    class WatchdogSupervisorTask(SupervisorTask):
        def start_task(self):
            from conductor.process import MixedProcess as Process
            from conductor.protocol.xmpp.watchdog import XMPPWatchdogPingTask, XMPPWatchdogPongTask
            
            p = Process()
            p.logger = open_logger(log_dir, "xmpp.proc.watchdog01.log", "xmpp.proc.watchdog01.logger")
            self.supervised.append(p)
            t = XMPPWatchdogPingTask(p.bus)
            t.settings.username = "watchdog01"
            t.settings.password = "test"
            t.settings.domain = "localhost"
            t.settings.resource = "localhost"
            t.settings.hostname = "localhost"
            t.settings.log_stdout = options.verbose
            t.proc_connection = ProcClient(("127.0.0.1", 12001), "secret")
            t.nodes = ['localhost']
            t.storage = MemcacheClient(['127.0.0.1:11211'])
            p.register_task(t)
            p.start()

            p = Process()
            p.logger = open_logger(log_dir, "xmpp.proc.watchdog02.log", "xmpp.proc.watchdog02.logger")
            self.supervised.append(p)
            t = XMPPWatchdogPongTask(p.bus)
            t.settings.username = "watchdog02"
            t.settings.password = "test"
            t.settings.domain = "localhost"
            t.settings.resource = "localhost"
            t.settings.hostname = "localhost"
            t.settings.log_stdout = options.verbose
            t.proc_connection = ProcClient(("127.0.0.1", 12001), "secret")
            t.storage = MemcacheClient(['127.0.0.1:11211'])
            p.register_task(t)
            p.start()

    from conductor.supervisor import Supervisor
    s = Supervisor()
    s.logger = open_logger(log_dir, "conductor.supervisor.log", 
                           "conductor.supervisor.logger")

    t = WatchdogSupervisorTask(s.bus)
    t.proc_connection = ProcListener(("127.0.0.1", 12001), "secret")
    s.register_task(t)

    s.run()
