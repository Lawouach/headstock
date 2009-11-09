# -*- coding: utf-8 -*-

__all__ = ['HeadstockError', 'HeadstockInvalidError', 
           'HeadstockStreamError', 'HeadstockAuthenticationFailure',
           'HeadstockInvalidStanzaError', 'HeadstockAuthenticationSuccess',
           'HeadstockSessionBound', 'HeadstockStartTLS']

class HeadstockError(StandardError):
    pass

class HeadstockInvalidError(HeadstockError):
    pass

class HeadstockStreamError(HeadstockError):
    pass

class HeadstockAuthenticationFailure(HeadstockError):
    pass

class HeadstockAuthenticationSuccess(HeadstockError):
    pass

class HeadstockInvalidStanzaError(HeadstockError):
    pass

class HeadstockSessionBound(HeadstockError):
    pass

class HeadstockStartTLS(HeadstockError):
    pass
