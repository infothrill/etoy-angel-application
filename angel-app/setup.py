#!/usr/bin/env python

import sys

def check_python():
    if sys.version_info < (2,4):
        print "Python 2.4 or higher is required to run Angel."
        sys.exit(256)

check_python()

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

VERSION = "0.4.6" # Update for every release 
DESCRIPTION = "ANGEL APPLICATION - long term peer to peer backup"
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
    # py2app does not (yet?) support multiple targets, which means that only the gui will be bundled but not the other scripts... ;-(
    #app = ['src/bin/angel.py', 'src/bin/master.py', 'src/bin/presenter.py', 'src/bin/provider.py', 'src/bin/maintainer.py'],
    app = ['src/bin/angel.py'],
    name="Angel",
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
                 #'angel_app' : 'src/angel_app'
                 '' : 'src'
                 },
    install_requires = [
                        "zope.interface>=3.3.0",
                        "netaddress>=0.2.2",
                        "pycrypto>=2.0.1",
                        "dyndnsc>=0.1.0",
                        ], 
    # for some unkown reason pycrypto gets bundled fine only if installed manually from its tarball (easy_install not so easy)
    # wxPython does not conform to cheeseshop.python.org standards, so currently we cannot include it here
    #dependency_links = [
    #    "http://angelapp.missioneternity.org/index.py/Documentation/Install?action=AttachFile&do=get&target=ezPyCrypto.py#egg=ezPyCrypto-0.1"
    #],
    zip_safe=False,
)
