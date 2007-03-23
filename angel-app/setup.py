#!/usr/bin/env python

import sys

def check_python():
    if sys.version_info < (2,4):
        print "Python 2.4 or higher is required to run Angel-App."
        sys.exit(256)

check_python()

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

VERSION = '0.1' # TODO: use version from angel_app.version.getVersionString()
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
    author="Vincent Kraeutler and Paul Kremer, etoy.VENTURE ASSOCIATION",
    author_email="vincent@etoy.com",
    url="http://angelapp.missioneternity.org/",
    license="MIT License",
    packages=find_packages('src'),
    platforms=['MacOS X', 'Linux', 'FreeBSD'],
    package_dir={
                 'angel_app' : 'src/angel_app'
                 },
    install_requires = ["xattr>=0.3", "zope.interface>=3.3.0", "pycrypto>=2.0.1"], #, "ezPyCrypto"],
    #dependency_links = [
    #    "http://angelapp.missioneternity.org/index.py/Documentation/Install?action=AttachFile&do=get&target=ezPyCrypto.py#egg=ezPyCrypto-0.1"
    #],
    zip_safe=False,
)

setup(
    name="twisted",
    version=2.5,
    description="twisted matrix",
    long_description="components of twisted used by angel-app, with minor modifications",
    classifiers=CLASSIFIERS,
    author="twisted crew",
    author_email="vincent@etoy.com",
    url="http://angelapp.missioneternity.org/",
    license="MIT License",
    packages=find_packages('contrib'),
    platforms=['MacOS X', 'Linux', 'FreeBSD'],
    package_dir={
                 'twisted' : 'contrib/twisted'
                 },
    install_requires = ["xattr>=0.3", "zope.interface>=3.3.0", "pycrypto>=2.0.1"],
    zip_safe=False,
)