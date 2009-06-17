#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path
import ConfigParser

from memcache import Client

class ZabbixMarkerPrinter(object):
    @staticmethod
    def run():
        conf = ConfigParser.ConfigParser()
        conf.readfp(file(os.path.join(os.path.dirname(__file__), 'watchdog.conf'), 'rb'))
        mc = Client([conf.get('run', 'memcached')])
        print mc.get(str(conf.get('run', 'memcached_key')))

if __name__ == '__main__':
    ZabbixMarkerPrinter.run()
