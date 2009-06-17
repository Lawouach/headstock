# -*- coding: utf-8 -*-
import time

from headstock.client.im import IMComponent
from headstock.client.presence import PresenceComponent
from headstock.client.roster import RosterComponent
from headstock.api.im import Message, Body, Event
from headstock.lib.utils import generate_unique

__all__ = ['MessagePingPong', 'RosterHandler', 'PresenceHandler']

class WatchdogSettings(object):
    def __init__(self):
        self.watchdog = None
        self.marker = None
        self.roster = None
        self.start = None

class MessagePingPong(IMComponent, WatchdogSettings):
    def __init__(self):
        super(MessagePingPong, self).__init__()
        self.ids = []
        self.roster = None

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
            m = Message(unicode(self.from_jid), unicode(message.from_jid), 
                        type=u'chat', stanza_id=message.stanza_id)
            m.bodies.append(Body(u'pong'))
            self.send(m, 'outbox')
            self.watchdog.succeeded()
        else:
            for body in message.bodies:
                marker = "%s_%s" % (self.marker, str(message.from_jid.resource))
                if body.plain_body != u'pong':
                    self.watchdog.store(marker, 100000)
                    self.watchdog.failed()
                else:
                    self.watchdog.store(marker, time.time() - self.start)
                    self.watchdog.succeeded(str(message.from_jid.resource), self.marker)
            self.ids.remove(message.stanza_id)

class PresenceHandler(PresenceComponent, WatchdogSettings):
    def __init__(self):
        super(PresenceComponent, self).__init__()

    def update_roster(self, roster):
        self.roster = roster

    def contact_available(self, p):
        if unicode(p.from_jid) != unicode(self.from_jid):
            marker = "%s_AVAILABLE_%s" % (self.marker, str(p.from_jid.resource))
            self.watchdog.store(marker, time.time() - self.start)
            self.watchdog.succeeded(str(p.from_jid.resource), self.marker)
        else:
            self.start = time.time()

    def contact_unavailable(self, p):
        if unicode(p.from_jid) != unicode(self.from_jid):
            marker = "%s_UNAVAILABLE_%s" % (self.marker, str(p.from_jid.resource))
            self.watchdog.store(marker, time.time() - self.start)

class RosterHandler(RosterComponent, WatchdogSettings):
    def __init__(self):
        super(RosterComponent, self).__init__()
        self.handlers = []
        
    def received_roster(self, roster):
        for handler in self.handlers:
            handler.update_roster(roster)
