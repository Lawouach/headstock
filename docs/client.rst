===============
Kamaelia client
===============

If you wish to use Kamaelia rather than the default
client you only need to do:

.. code-block :: python 

    from headstock.client import KamaeliaClient
    c = KamaeliaClient(u'user@domain', u'secret', hostname='localhost', port=5222)
    c.set_log(stdout=True)
    c.run()

==============
Tornado client
==============

If you wish to use Kamaelia rather than the default
client you only need to do:

.. code-block :: python 

    from headstock.client import TornadoClient
    c = TornadoClient(u'user@domain', u'secret', hostname='localhost', port=5222)
    c.set_log(stdout=True)
    c.run()

If you prefer that the client doesn't start the Tornado
ioloop itself, use the following instead:

.. code-block :: python 

    c.run(start_loop=False)
