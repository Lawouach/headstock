# -*- coding: utf-8 -*-
import time

from headstock.client.im import IMComponent
from headstock.client.roster import RosterComponent
from headstock.api.im import Message, Body, Event
from headstock.lib.utils import generate_unique

__all__ = ['MessagePingPong', 'RosterHandler']

class WatchdogSettings(object):
    def __init__(self):
        self.watchdog = None
        self.marker = None

class MessagePingPong(IMComponent, WatchdogSettings):
    def __init__(self):
        super(MessagePingPong, self).__init__()
        self.ids = []
        self.roster = None

        self.start = None

    def update_roster(self, roster):
        self.roster = roster

        for nodeid in roster.items:
            self.send_message(nodeid, u"ping")

    def send_message(self, jid, text):
        m = Message(unicode(self.from_jid), unicode(jid), 
                    type=u'chat', stanza_id=generate_unique())
        m.bodies.append(Body(unicode(text)))
        self.ids.append(m.stanza_id)
        self.start = time.time()
        self.send(m, "outbox")

    def received_message(self, message):
        if message.stanza_id not in self.ids:
            message.swap_jids()
            message.bodies = [Body(u'pong')]
            message.foreign = []
            self.send(message, 'outbox')
            self.watchdog.succeeded()
        else:
            for body in message.bodies:
                if body.plain_body != u'pong':
                    self.watchdog.failed()
                else:
                    self.watchdog.store(self.marker, time.time() - self.start)
                    self.watchdog.succeeded()
            self.ids.remove(message.stanza_id)

class RosterHandler(RosterComponent, WatchdogSettings):
    def __init__(self):
        super(RosterComponent, self).__init__()
        self.handlers = []
        
    def received_roster(self, roster):
        for handler in self.handlers:
            handler.update_roster(roster)
