#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import ConfigParser

from memcache import Client

class ZabbixMarkerPrinter(object):
    @staticmethod
    def run(options):
        conf = ConfigParser.ConfigParser()
        conf.readfp(file(os.path.join(os.path.dirname(__file__), 'watchdog.conf'), 'rb'))
        mc = Client([conf.get('run', 'memcached')])
        print mc.get("%s_%s" % (options.marker, options.node)) 

if __name__ == '__main__':
    def parse_commandline():
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-n", "--node", dest="node",
                          help="Target node name")
        parser.add_option("-m", "--marker", dest="marker", 
                          help="Marker to lookup")
        (options, args) = parser.parse_args()

        return options

    options = parse_commandline()
    ZabbixMarkerPrinter.run(options)
