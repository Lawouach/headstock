# -*- coding: utf-8 -*-

__all__ = ['Microblog', 'MICROBLOG_SESSION_PROFILE']

MICROBLOG_SESSION_PROFILE = 'mic_profile_session'

class Microblog(object):
    def __init__(self):
        self.profile = None
