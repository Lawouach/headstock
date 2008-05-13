# -*- coding: utf-8 -*-
import cherrypy
import os
from amplee.indexer import *

__all__ = ['setup_atompub']

def setup_index(base_dir):
    index = Indexer()
    container = ShelveContainer(os.path.join(base_dir, 'index.p'))
    index.register(PublishedIndex('pi', container=container, granularity=DateIndex.day))
    index.register(UpdatedIndex('ui', container=container, granularity=DateIndex.minute))
    index.register(EditedIndex('ei', container=container, granularity=DateIndex.minute))
    index.register(AuthorIndex('ai', container=container, index_email=True, index_uri=True))
    index.register(CategoryIndex('ci', container=container))
    
    return index


def setup_atompub(base_dir): 
    d = cherrypy.dispatch.RoutesDispatcher()   
    cherrypy.config.update({'engine.autoreload_on' : False,
                            'server.socket_port' : 8080, 
                            'server.socket_host': '127.0.0.1',
                            'server.socket_queue_size': 15,
                            'log.screen': True,
                            'log.access_file': os.path.join(base_dir, 'access.log'),
                            'log.error_file': os.path.join(base_dir, 'error.log'),
                            'checker.on': False,})

    index = setup_index(base_dir)

    from cherrypy._cpdispatch import MethodDispatcher
    from microblog.web.atompub import Application
    atompub = Application(base_dir, index, dispatcher=d)

    d.connect('main', ':action', controller=atompub)
    cherrypy.tree.mount(atompub, '/', {'/': { 'request.dispatch': d,
                                              'tools.etags.on': True,
                                              'tools.etags.autotags': False},
                                       '/static': {'tools.staticdir.on': True,
                                                   'tools.staticdir.dir': os.path.join(base_dir, 'static')}})

    return atompub
    
