import os
import cPickle
import shutil

from zope.interface import implements
from twisted.python.filepath import FilePath

from angel_app.config.config import getConfig
from angel_app.resource.IDeadPropertyStore import IDeadPropertyStore
from angel_app.singlefiletransaction import SingleFileTransaction
from angel_app.log import getLogger

log = getLogger(__name__)

# the root of the angel-app directory tree
home = getConfig().get("common","angelhome")

# refuse to load the module unless the root exists
assert os.path.exists(home), \
    "refusing to load the module unless the root exists: " + `home`

# where we store file data
metadata = home + os.sep + "metadata"

if not os.path.exists(metadata):
    log.info("Creating root directory for meta data: %r", metadata)
    os.mkdir(metadata)
     
    
class DirectoryDeadProperties(object):
    """
    An implementation of a DeadPropertyStore (i.e. store for persistent properties).
    We store the dead properties in a directory tree _parallel_ to the resource tree.
    The path to a resource's metadata relative to the root of the metadata directory tree
    is the same as the path of the resource content relative to the repository root.
    Every resource's metadata is represented as a directory: every metadata entry is 
    represented as a file pickle in that directory.
    """
    implements(IDeadPropertyStore)
    
    def __init__(self, _resource):
        self.resource = _resource
        self.metadataPath = FilePath(metadata + os.sep + self.resource.relativePath())
        self.__sanitize()
    
    def _fileNameFor(self, qname):
        """
        @return: a file name for a property of this resource
        """
        return self.metadataPath.path + os.sep + qname[1]
    
    def __sanitize(self):
        """
        The problem we're trying to address here (rather than simply putting it into the constructor) 
        is that seemingly, in twisted, an object's method may be called _before_ the constructor has
        returned (if the constructor is doing some non-blocking shizzle, that is).
        So we provide a separate file system sanity check which we call before every call to this
        that hits the file system, to e.g. ensure that the containing directory exists.
        """
        # perform sanity check:
        if os.path.exists(self.metadataPath.path):
            assert self.metadataPath.isdir(), \
                "metadata store must be a directory: " + self.metaDataPath.path
        else:
            log.info("Creating metadata store for: %s", self.metadataPath.path)
            os.mkdir(self.metadataPath.path)
        
    def get(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """
        self.__sanitize()
        return cPickle.load(open(self._fileNameFor(qname)))

    def set(self, property):
        """
        @param property -- an instance of twisted.web2.dav.davxml.WebDAVElement
        """
        self.__sanitize()
        transaction = SingleFileTransaction()
        try:
            f = transaction.open(self._fileNameFor(property.qname()), 'wb')
            cPickle.dump(property, f)
            f.close()
        except Exception, e:
            transaction.cleanup()
            log.warn("A problem occured while saving property %s:", property.qname(), exc_info = e)
            raise
        else:
            transaction.commit()
        
    def delete(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """
        self.__sanitize()
        os.remove(self._fileNameFor(qname))

    def contains(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """
        # hm, if the pickle file is corrupt, we should not return true...
        # I think it is good style to define that if contains() is true, get()
        # should not crash.
        # TODO: optimize?
        # Therefore, even if slow, we try get() in order to figure out contains():
        self.__sanitize()
        fileNames = os.listdir(self.metadataPath.path)
        if qname[1] in fileNames:
            try:
                self.get(qname)
            except Exception, e:
                log.debug("Error on contains(%r) -> assume non existant", qname, exc_info = e)
                return False
            else:
                return True
        else:
            return False

    def list(self):
        """
        """
        self.__sanitize()
        return [("DAV:", fileName) for fileName in os.listdir(self.metadataPath.path)]
    
    def remove(self):
        """
        Remove this entry from the data base.
        """
        shutil.rmtree(self.metadataPath.path, ignore_errors = True)
        