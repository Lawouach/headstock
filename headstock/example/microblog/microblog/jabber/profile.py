# -*- coding: utf-8 -*-
from urlparse import urlparse

from Axon.Component import component
from Axon.Ipc import shutdownMicroprocess, producerFinished
from Kamaelia.Protocol.HTTP.HTTPClient import SimpleHTTPClient

from microblog.jabber.client import Client
from microblog.profile.manager import ProfileManager

__all__ = ['ProfileHandler', 'NewProfileHandler']

class NewProfileHandler(component):
    Inboxes = {"inbox"   : "",
               "control" : "Shutdown the client stream",
               "_response": ""}
    
    Outboxes = {"outbox" : "",
                "signal" : "Shutdown signal",
                "log"    : "log",
                "_request": ""}
    
    def __init__(self, base_dir, atompub):
        super(NewProfileHandler, self).__init__()
        self.base_dir = base_dir
        self.atompub = atompub

    def initComponents(self):
        self.client = SimpleHTTPClient()
        self.addChildren(self.client)
        self.link((self, '_request'), (self.client, 'inbox')) 
        self.link((self.client, 'outbox'), (self, '_response')) 
        self.client.activate()

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                feed = self.recv('inbox')
                for entry in feed.entries:
                    for link in entry.links:
                        if link.rel == 'edit-media' and link.type == 'application/xml':
                            profile_name = urlparse(link.href)[2].rsplit('/', -1)[-1]
                            pwd = ProfileManager.set_profile_password(self.base_dir, profile_name)
                            profile = ProfileManager.load_profile(self.base_dir, self.atompub, profile_name)
                            Client.register_jabber_user(self.atompub, profile_name.lower(), pwd, profile)

                            params = {'url': link.href, 'method': 'DELETE'}
                            self.send(params, '_request') 
                            
                            continue
                
            if not self.anyReady():
                self.pause()
  
            yield 1

class ProfileHandler(component):
    Inboxes = {"inbox"   : "",
               "control" : "Shutdown the client stream",
               "_response": ""}
    
    Outboxes = {"outbox" : "",
                "signal" : "Shutdown signal",
                "log"    : "log",
                "_request": ""}
    
    def __init__(self, base_dir, atompub):
        super(ProfileHandler, self).__init__()
        self.base_dir = base_dir
        self.atompub = atompub

    def initComponents(self):
        self.client = SimpleHTTPClient()
        self.addChildren(self.client)
        self.link((self, '_request'), (self.client, 'inbox')) 
        self.link((self.client, 'outbox'), (self, '_response')) 
        self.client.activate()

    def main(self):
        yield self.initComponents()

        while 1:
            if self.dataReady("control"):
                mes = self.recv("control")
                
                if isinstance(mes, shutdownMicroprocess) or \
                        isinstance(mes, producerFinished):
                    self.send(producerFinished(), "signal")
                    break

            if self.dataReady("inbox"):
                feed = self.recv('inbox')
                for entry in feed.entries:
                    for link in entry.links:
                        if link.rel == 'edit-media' and link.type == 'application/xml':
                            profile_name = urlparse(link.href)[2].rsplit('/', -1)[-1]
                            pwd = ProfileManager.get_profile_password(self.base_dir, profile_name)
                            profile = ProfileManager.load_profile(self.base_dir, self.atompub, profile_name)
                            if not Client.get_status(profile_name):
                                Client.connect_jabber_user(self.atompub, profile_name.lower(), pwd, profile)

                            continue

            if not self.anyReady():
                self.pause()
  
            yield 1

