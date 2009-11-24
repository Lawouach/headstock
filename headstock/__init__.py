# -*- coding: utf-8 -*-
__version__ = "0.4.1"
__authors__ = ["Sylvain Hellegouarch (sh@defuze.org)"]
__copyright__ = """
Copyright (c) 2006, 2007, 2008, 2009 Sylvain Hellegouarch
All rights reserved.
"""
__license__ = """
Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:
 
     * Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
     * Redistributions in binary form must reproduce the above copyright notice, 
       this list of conditions and the following disclaimer in the documentation 
       and/or other materials provided with the distribution.
     * Neither the name of Sylvain Hellegouarch nor the names of his contributors 
       may be used to endorse or promote products derived from this software 
       without specific prior written permission.
 
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND 
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

__all__ = ['xmpphandler']

def xmpphandler(name, ns, once=False, forget=True):
    """
    Decorator to wrap a callable so that it can be used as
    a XMPP handler by the headstock client.

    It will set various attributes to the wrapped callable:

    * handler: set to `True` to indicate the callable can participate to the dispatching
    * xmpp_local_name: XML element name
    * xmpp_ns: XML element namespace
    * fire_once: if `True`, this handler will be removed once it has been used.
    * forget: if set to `True`, the dispatched element will be automatically deleted once the handler has been called.

    ``name`` XMPP stanza name

    ``ns`` XMPP stanza namespace

    ``once`` False - flag indicating if the handler should
    be called only once and unregistered automatically

    ``forget`` True - flag indicating if the dispatched
    :class:`bridge.Element` instance should be automatically
    forgotten once dispatched.
    """
    def wrapper(func):
        func.handler = True
        func.fire_once = once
        func.forget = forget
        func.xmpp_local_name = name
        func.xmpp_ns = ns
        return func
    return wrapper
