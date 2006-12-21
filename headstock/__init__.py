#!/usr/bin/env python
# -*- coding: utf-8 -*-

def register(operation):
    """
    Simply set the 'headstock' attribute to the callable
    with the name of the operation
    """
    def outter(func):
        if not hasattr(func, 'headstock'):
            func.headstock = operation
        return func
    return outter
