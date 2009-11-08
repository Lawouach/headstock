.. _getting_started:

============
Requirements
============

Minimum
=======
* Python 2.5+
* bridge 0.4.0+ http://trac.defuze.org/wiki/bridge
* ssl 1.15+ (for TLS support) http://pypi.python.org/pypi/ssl

Kamaelia
========
If you want to run the Kamaelia client:

* Kamaelia 0.9.6+ http://www.kamaelia.org/Home

Tornado
=======
If you want to run the Tornado client:

* Tornado 0.2+ http://www.tornadoweb.org/

==========
Installing
==========

From a packaged release
=======================

.. code-block:: bash 

   $ easy_install -U headstock


From the source code 
=====================

.. code-block:: bash 
   
   $ svn co https://svn.defuze.org/oss/headstock/ headstock-trunk
   $ cd headstock-trunk 
   $ python setup.py install

================
Running examples
================

Basic example
=============

In order to run the basic example and see if the installation went well:

.. code-block:: bash 

   $ cd headstock-trunk/example
   $ python basic.py -j username@domain -p secret

Replace the jid and password with an appropriate account.

Pubsub example
==============

The pubsub example runs against any pubsub service but is
notable specialized against a superfeedr service: http://superfeedr.com/

.. code-block:: bash 

   $ cd headstock-trunk/example
   $ python basic.py -j username@domain -p secret -a firehoser.superfeedr.com:5222

Make sure you replace the jid and password with a valid superfeedr account.
