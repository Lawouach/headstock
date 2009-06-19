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
        (options, args) = parser.parse_args()

        return options
    options = parse_commandline()

    from conductor.lib.logger import open_logger, close_logger
    from conductor.connection import ProcClient, ProcListener

    from conductor.supervisor import SupervisorTask
    class WatchdogSupervisorTask(SupervisorTask):
        def start_task(self):
            from conductor.protocol.xmpp import XMPPProcess
            p = XMPPProcess()
            p.logger = open_logger(log_dir, "xmpp.proc.watchdog01.log", "xmpp.proc.watchdog01.logger")
            self.supervised.append(p)

            from conductor.protocol.xmpp.watchdog import XMPPWatchdogPingTask, XMPPWatchdogPongTask
            t = XMPPWatchdogPingTask(self.bus)
            t.settings.username = "watchdog01"
            t.settings.password = "test"
            t.settings.domain = "localhost"
            t.settings.resource = "localhost"
            t.settings.hostname = "localhost"
            t.proc_connection = ProcClient(("127.0.0.1", 12001), "secret")
            t.nodes = ['localhost']
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
