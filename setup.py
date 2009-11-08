"""
XMPP library
"""

#from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
from setuptools import setup
 
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']
        
setup(name = "headstock",
      version = '0.4.0',
      description = "XMPP library",
      maintainer = "Sylvain Hellegouarch",
      maintainer_email = "sh@defuze.org",
      url = "http://trac.defuze.org/wiki/headstock",
      download_url = "http://www.defuze.org/oss/headstock/",
      packages = ["headstock", "headstock.lib", "headstock.lib.auth"],
      platforms = ["any"],
      license = 'BSD',
      long_description = "XMPP library",
      install_requires= ['bridge>=0.4.0'],
      zip_safe=False
     )

