#!/usr/bin/env python
"""
Patch Info.plist to have correct information
See http://developer.apple.com/documentation/MacOSX/Conceptual/BPRuntimeConfig/index.html for more information
"""

from optparse import OptionParser
from os import path
import plistlib
import sys

NAME = "Angel"

parser = OptionParser()
parser.add_option("-v", "--version", dest="version", help="version string", default=None)
parser.add_option("-b", "--buildnumber", dest="buildnumber", help="buildnumber", default=None)
(options, args) = parser.parse_args()

if len(args) < 1:
    print "Please provide the path to the application bundle!"
    sys.exit()

PATH_TO_BUNDLE=args[0]
PLIST_FILE=path.join(PATH_TO_BUNDLE, "Contents", "Info.plist")

if not path.exists(PLIST_FILE):
    print "plist file '%s' not found" % PLIST_FILE
    sys.exit()

if options.version == None:
    print "Please provide a version using --version"
    sys.exit()

if options.buildnumber == None:
    print "Please provide a build number using --buildnumber"
    sys.exit()

plist = plistlib.readPlist(PLIST_FILE)

plist.update(
         dict(
                CFBundleShortVersionString = options.version,
                CFBundleVersion = options.buildnumber,
                CFBundleGetInfoString = ' '.join([NAME, options.version]),
                CFBundleIdentifier = 'org.missioneternity.angel',
             )
 )

plistlib.writePlist(plist, PLIST_FILE)

