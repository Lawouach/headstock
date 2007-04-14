"""
Some XMPP extensions
"""

#from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup
 
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']
        
setup(name = "headstock",
      version = '0.1.0',
      description = "Some XMPP extensions",
      maintainer = "Sylvain Hellegouarch",
      maintainer_email = "sh@defuze.org",
      url = "http://trac.defuze.org/wiki/headstock",
      download_url = "http://www.defuze.org/oss/headstock/",
      packages = ["headstock", "headstock.protocol",
                  "headstock.protocol.extension",
                  "headstock.protocol.core", "headstock.lib",
                  "headstock.lib.auth", "headstock.lib.network",
                  "headstock.api"],
      platforms = ["any"],
      license = 'BSD',
      long_description = "",
     )

