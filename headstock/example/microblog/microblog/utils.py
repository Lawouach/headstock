# -*- coding: utf-8 -*-

from amplee.utils import parse_isodate

__all__ = ['format_date']

def format_date(dt, format='%a, %d %b %Y %H:%M'):
    d = parse_isodate(dt)
    return d.strftime(format)
