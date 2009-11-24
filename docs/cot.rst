==================
Cot script support
==================

headstock allows you to run cot scripts as used by
the `Tigase server <https://svn.tigase.org/reps/tigase-testsuite/trunk/tests/data/>`_.

Cot scripts are useful to perform task in a declarative way. You can use them
for testing or for automated jobs.

Using cot scripts
=================

Using the cot handler requires a running instance of 
the `CherryPy process bus <http://www.cherrypy.org/wiki/WSPBSpec>`_.

First we get a list of scripts from the filesystem:

>>> import os, os.path
>>> from glob import iglob
>>> scripts = iglob(os.path.join(os.curdir, 'cots', '*.cot'))

Create a bus instance.

>>> from cherrypy.lib.process.wspbus import Bus
>>> bus = Bus()

Create and register and instance of the cot handler.

>>> from headstock.lib.cot import Cot
>>> client.register(Cot(bus, scripts))

Finally you start the bus instance and block.

>>> bus.start()
>>> bus.block(interval=0.002)

Note that you need to block because the cot handler
will process loaded stanzas within the loop of the bus.

Depending on which client you've decided to use, this
may be a problem because the client needs also its own loop.

For the client based on asyncore, you may therefore do
something like this prior to starting the bus:

>>> import select
>>> if hasattr(select, "poll"):
>>>    from asyncore import poll2
>>>    poll = poll2
>>> else:
>>>    from asyncore import poll
>>> bus.subscribe("main", poll, timeout=30.0)

For tornado and kamaelia, you might probably 
do something similar or alternatively look at 
the `conductor <http://trac.defuze.org/wiki/conductor>`_ project.
