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

log = logging.getLogger('srcamber-droplet')

class ScrambledDirectory(object):
    """
    A class that should come in handy when wanting to take a file and scramble
    its filename, while copying it into a destination folder.
    """
    def __init__(self, id, targetpath):
        """
        
        @param id: the capsule ID
        @param targetpath: the capsule folder, must exist 
        """
        self._id = id
        assert os.path.isdir(targetpath), "The directory '%s' for the capsule does not exist" % targetpath
        self._targetpath = targetpath
        self.EXCLUDE_FILES = [ '.DS_Store', 'Thumbs.db' ]

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
        assert os.path.getsize(sourcefilename) > 0, "The given file '%s' has 0 size!" % sourcefilename
        sourcebasefilename = os.path.basename(sourcefilename)
        if sourcebasefilename in self.EXCLUDE_FILES:
            log.warn("excluding file '%s'" % sourcefilename)
            return 0
        sourcechecksum = self._checksum(sourcefilename)
        targetbasefilename = self._generateFilename(sourcefilename, sourcechecksum) 
        targetfilename = os.path.join(self._targetpath, targetbasefilename)
        if os.path.isfile(targetfilename):
            log.info("Skipping '%s', already present" % targetbasefilename)
            return 0
        log.info("\t%s from '%s'" % (targetbasefilename, sourcebasefilename))
        try:
            shutil.copy(sourcefilename, targetfilename)
        except Exception, e:
            log.error("got an exception while adding file %s to capsule %s: %s" % (sourcefilename, targetfilename), exc_info =e)
            try:
                os.unlink(targetfilename)
            except:
                pass
        os.chmod(targetfilename, 0444) # make target read-only / pure paranoia
        assert self._checksum(targetfilename) == sourcechecksum, "After copying, the checksum changed"


def findId():
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

    capsule = ScrambledDirectory(capsuleid, capsulepath)

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