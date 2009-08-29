#!/usr/bin/env python

"""
Minimal python script that can be used to scramble files from the command line
as well as being built as a "droplet" application for OS X.

Input files need to comply to the following:
- existing file extension
- non-zero file length
"""

import sys
import re
import os
import hashlib
import shutil
from optparse import OptionParser
import logging

log = logging.getLogger('scrambler-droplet')

import scramble

def findId():
    """
    tool to find the ARCANUM ID based on the name of the .app bundle on disk
    """
    thispath = sys.argv[0]
    print thispath
    reg = re.compile("\.app")
    if reg.search(thispath):
        doSearch = True
    else:
        doSearch = False
    id = None
    while doSearch:
        part1, part2 = os.path.split(thispath)
        if part2.endswith(".app"):
            doSearch = False
            id, ext = os.path.splitext(part2)
        thispath = part1

    if id is None:
        raise Exception, "Could not find an ID, either run with command line options or as a drop target on a .app bundle"
    return thispath, id

def main():
    parser = OptionParser()
    parser.add_option("--capsuleid", dest="capsuleid", help="capsule id", default=None)
    parser.add_option("--targetbasepath", dest="targetbasepath", help="target base path to contain the capsule folder", default=None)
    (options, args) = parser.parse_args()

    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')

    # detect target base path (where to put the capsule folder)
    # detect the capsule id
    if options.capsuleid is None: # Droplet mode
        cwdpath, capsuleid = findId()
    else: # command line mode
        capsuleid = options.capsuleid
        if options.targetbasepath is None:
            cwdpath = os.getcwd()
        else:
            cwdpath = options.targetbasepath

    if len(args) == 0:
        log.warn("no files given, nothing to scramble")
        return 1
    capsulepath = os.path.join(cwdpath, capsuleid)
    if not os.path.exists(capsulepath):
        os.mkdir(capsulepath)

    capsule = scramble.ScrambledDirectory(capsuleid, capsulepath)

    for arg in args:
        if os.path.isdir(arg):
            for root, dirs, files in os.walk(arg):
                for name in files:
                    srcfilename = os.path.join(root, name)
                    capsule.addFile(srcfilename)
        elif os.path.isfile(arg):
            srcfilename = arg
            capsule.addFile(srcfilename)

    return 0

if __name__ == '__main__':
    sys.exit(main())