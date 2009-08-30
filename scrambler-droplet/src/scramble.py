import os
import shutil
import logging
import mimetypes
import sha

log = logging.getLogger('ScrambledDirectory')

def m221estreamchecksum(stream):
    hasher = sha.new()
    hasher.update(stream.read())
    return hasher.hexdigest()

def m221echecksum(filename):
    stream = open(filename, 'rb')
    res = m221estreamchecksum(stream)
    stream.close()
    return res

def getExtension(fname, mimetype = None):
    """
    this is a wrapper to find an extension of a filename. Optionally, a mimetype
    can be specified in order to try to find a good extension harder.

    @param fname: filename
    @param mimetype: a mimetype
    """
    dummybasename, extension = os.path.splitext(fname)
    if len(extension) == 0:
        if not mimetype is None:
            extension = mimetypes.guess_extension(mimetype) # includes leading dot, nice!
            if extension is None:
                return ''
    return extension
    
def hasExtension(fname, mimetype = None):
    return len(getExtension(fname, mimetype)) > 0 

def generateFilename(id, fname, checksum, mimetype = None):
    """
    generates a "scrambled" filename based on the given id, filename and the
    given checksum
    """
    assert hasExtension(fname, mimetype), "Cowardly refusing to scramble a file that has no extension: '%s'" % fname
    extension = getExtension(fname).lower()
    return checksum + "-" + id + extension

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

    def addFile(self, sourcefilename, mimetype = None):
        assert os.path.isfile(sourcefilename), "The given filename is not a file: '%s'" % sourcefilename
        assert os.path.getsize(sourcefilename) > 0, "The given file '%s' has 0 size!" % sourcefilename
        sourcebasefilename = os.path.basename(sourcefilename)
        if sourcebasefilename in self.EXCLUDE_FILES:
            log.warn("excluding file '%s'" % sourcefilename)
            return 0
        sourcechecksum = m221echecksum(sourcefilename)
        targetbasefilename = generateFilename(self._id, sourcefilename, sourcechecksum, mimetype) 
        targetfilename = os.path.join(self._targetpath, targetbasefilename)
        if os.path.isfile(targetfilename):
            log.info("Skipping '%s', already present" % targetbasefilename)
            return 0
        log.info("\t%s from '%s'" % (targetbasefilename, sourcebasefilename))
        try:
            shutil.copy(sourcefilename, targetfilename)
        except Exception, e:
            log.error("got an exception while adding file %s to capsule %s: %s" % (sourcefilename, targetfilename), exc_info = e)
            try:
                os.unlink(targetfilename)
            except OSError, e:
                log.error("Failed to cleanup error after adding file to capsule", exc_info = e)
        os.chmod(targetfilename, 0444) # make target read-only / pure paranoia
        if not m221echecksum(targetfilename) == sourcechecksum:
            os.unlink(targetfilename)
            raise ValueError, "After copying, the checksum changed!"

