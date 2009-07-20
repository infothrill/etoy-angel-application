#!/usr/bin/env python
"""
setup.py - script for building MyApplication
"""
from distutils.core import setup
import py2app

NAME = 'Scrambler Droplet'
VERSION = '1.1'

plist = dict(
    #CFBundleIconFile='scrambler_icon.icns',
    CFBundleName=NAME,
    CFBundleVersion=VERSION,
    CFBundleShortVersionString=VERSION,
    CFBundleGetInfoString=' '.join([NAME, VERSION]),
    CFBundleExecutable=NAME,
    CFBundleIdentifier='org.missioneternity.scrambler-droplet',
)


# Note that you must replace hypens '-' with underscores '_'
# when converting option names from the command line to a script.
# For example, the --argv-emulation option is passed as 
# argv_emulation in an options dict.
py2app_options = dict(
    # Map "open document" events to sys.argv.
    # Scripts that expect files as command line arguments
    # can be trivially used as "droplets" using this option.
    # Without this option, sys.argv should not be used at all
    # as it will contain only Mac OS X specific stuff.
    argv_emulation=True,

    # This is a shortcut that will place MyApplication.icns
    # in the Contents/Resources folder of the application bundle,
    # and make sure the CFBundleIcon plist key is set appropriately.
    iconfile='scrambler_icon.icns',
)

setup(
    app = ['scrambler-droplet.py'],
    plist = plist,
    options=dict(
        # Each command is allowed to have its own
        # options, so we must specify that these
        # options are py2app specific.
        py2app=py2app_options,
    ),
    version = VERSION,
)
