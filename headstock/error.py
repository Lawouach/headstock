#!/usr/bin/env python
# -*- coding: utf-8 -*-

class HeadstockError(StandardError):
    pass

class HeadstockInvalidError(HeadstockError):
    pass

class HeadstockStreamError(HeadstockError):
    pass

class HeadstockAuthenticationFailure(HeadstockError):
    pass
