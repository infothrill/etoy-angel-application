#!/usr/bin/env python

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup #, Extension

import pkg_resources 

from pkg_resources import require 
require("xattr>=0.3")
require("zope.interface>=3.3.0")
require("pycrypto>=2.0.1")
#require("twisted>=2.5")

VERSION = '0.1'
DESCRIPTION = "The angel-app distributed file system."
LONG_DESCRIPTION = """
See http://angelapp.missioneternity.org/
"""

CLASSIFIERS = filter(None, map(str.strip,
"""                 
Environment :: Console
Intended Audience :: Developers
License :: OSI Approved :: GPL
License :: OSI Approved :: MIT License
Natural Language :: English
Operating System :: MacOS :: MacOS X
Operating System :: POSIX :: Linux
Operating System :: POSIX :: FreeBSD
Programming Language :: Python
Topic :: Software Development :: Libraries :: Python Modules
""".splitlines()))

setup(
    name="angel_app",
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    author="Vincent Kraeutler, etoy.VENTURE ASSOCIATION",
    author_email="vincent@etoy.com",
    url="http://angelapp.missioneternity.org/",
    license="MIT License",
    packages=['angel_app'],
    platforms=['MacOS X', 'Linux', 'FreeBSD'],
    package_dir={'angel_app': 'src/angel_app'},
    #install_requires = ["xattr>=0.3", "zope.interface>=3.3.0", "pycrypto>=2.0.1", "Twisted>=2.5"],
    install_requires = ["xattr>=0.3", "zope.interface>=3.3.0", "pycrypto>=2.0.1"],
#    ext_modules=[
#        Extension("xattr._xattr", ["Modules/xattr/_xattr.c"]),
#    ],
#    entry_points={
#        'console_scripts': [
#            "xattr = xattr.tool:main",
#        ],
#    },
    zip_safe=False,
)
