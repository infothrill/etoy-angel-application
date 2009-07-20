#!/usr/bin/env python

"""
Minimal python script that can be used to scramble files from the command line
as well as being built as a "droplet" application for OS X.
"""

import sys
import os
import hashlib
import shutil
from optparse import OptionParser

class Capsule(object):
    def __init__(self, id, targetpath):
        """
        
        @param id: the capsule ID
        @param targetpath: the capsule folder, must exist 
        """
        self._id = id
        assert os.path.isdir(targetpath)
        self.targetpath = targetpath

    def _checksum(self, fname):
        hasher = hashlib.sha1()
        inputf = open(fname, 'rb')
        hasher.update(inputf.read())
        inputf.close()
        return hasher.hexdigest()
        
    def _generateFilename(self, fname, checksum):
        """
        generates a "scrambled" filename based on the given filename and the
        given checksum
        """
        basename, extension = os.path.splitext(fname)
        if len(extension) < 1:
            raise ValueError, "Cowardly refusing to scramble a file that has no extension: '%s'" % fname 
        extension = extension.lower()
        return checksum + "-" + self._id + extension
    
    def addFile(self, sourcefilename):
        assert os.path.isfile(sourcefilename), "The given filename is not a file: '%s'" % sourcefilename
        sourcebasefilename = os.path.basename(sourcefilename)
        EXCLUDE_FILES = [ '.DS_Store', 'Thumbs.db' ]
        if sourcebasefilename in EXCLUDE_FILES:
            print "WARN: excluding file '%s'" % sourcefilename
            return 0
        sourcechecksum = self._checksum(sourcefilename)
        targetbasefilename = self._generateFilename(sourcefilename, sourcechecksum) 
        targetfilename = os.path.join(self.targetpath, targetbasefilename)
        if os.path.isfile(targetfilename):
            print "DEBUG: Skipping '%s', already present" % targetbasefilename
            return 0
        print "\t%s from '%s'" % (targetbasefilename, sourcebasefilename)
        try:
            shutil.copy(sourcefilename, targetfilename)
        except Exception, e:
            print "ERROR: got an exception while adding file %s to capsule %s: %s" % (sourcefilename, targetfilename, str(e))
            try:
                os.unlink(targetfilename)
            except:
                pass
        os.chmod(targetfilename, 0444)
        assert self._checksum(targetfilename) == sourcechecksum


def getId():
    path = sys.argv[0]
    doSearch = True
    id = None
    while doSearch:
        part1, part2 = os.path.split(path)
        if part2.endswith(".app"):
            doSearch = False
            id, ext = os.path.splitext(part2)
        path = part1

    if id is None:
        raise Exception, "Could not find an ID"
    return path, id

def main():
    parser = OptionParser()
    parser.add_option("--capsuleid", dest="capsuleid", help="capsule id", default=None)
    parser.add_option("--targetbasepath", dest="targetbasepath", help="target base path to contain the capsule folder", default=None)
    (options, args) = parser.parse_args()

    # detect target base path (where to put the capsule folder)
    # detect the capsule id
    if options.capsuleid is None: # Droplet mode
        cwdpath, capsuleid = getId()
    else: # command line mode
        capsuleid = options.capsuleid
        if options.targetbasepath is None:
            cwdpath = os.getcwd()
        else:
            cwdpath = options.targetbasepath

    if len(args) == 0:
        print "WARN: no arguments given, nothing to scramble"
        return 1
    capsulepath = os.path.join(cwdpath, capsuleid)
    if not os.path.exists(capsulepath):
        os.mkdir(capsulepath)

    capsule = Capsule(capsuleid, capsulepath)

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