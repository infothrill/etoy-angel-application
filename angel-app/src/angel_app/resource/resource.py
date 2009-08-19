import os
import stat
from logging import getLogger

from angel_app import elements
from angel_app.contrib.ezPyCrypto import key as ezKey
from angel_app.resource import IResource
from angel_app.resource import util
from zope.interface import implements
from angel_app.io import RateLimit
from angel_app.io import bufferedReadLoop
from angel_app.resource.remote import exceptions as cloneExceptions

from angel_app.config.config import getConfig

log = getLogger(__name__)

cfg = getConfig()

MAX_DOWNLOAD_SPEED = cfg.getint('common', 'maxdownloadspeed_kib') * 1024 # internally handled in bytes

HTTP_BUFSIZE = 4096
LOCAL_BUFSIZE = 16384

class Resource(object):
    """
    Provide implementation of resource methods common to both local and remote resources.
    The key methods that need to be implemented are 
    -- getPropertyManager() which must return an object that behaves like a 
        twisted.web2.dav.xattrprops.xattrPropertyStore and handles resource metadata
        
    -- getContentManager() which must return a file-like object from which we can read the resource contents.
    """
    
    implements(IResource.IAngelResource)
    
    def getPropertyManager(self):
        """
        @see: IReadOnlyPropertyManager
        """
        raise NotImplementedError("Must be provided by subclass")
    
    def getContentManager(self):
        """
        @see: IReadOnlyContentManager
        """
        raise NotImplementedError("Must be provided by subclass")

    def open(self):
        """
        @return a stream-like object that has the read() and close() methods, to read the contents of the local resource
        """
        return self.getContentManager().open()
    
    def isCollection(self):
        return self.getPropertyManager().isCollection()

    def contentLength(self):
        return self.getContentManager().contentLength() 
        
    def getProperty(self, element):
        """
        Return a resource property by element.
        """
        try:
            return self.getPropertyManager().getByElement(element)
        except cloneExceptions.CloneIOError, e:
            # don't log complete exception, just notify IO problem
            log.debug("Failed to look up meta data field %r: %r" % (repr(element), repr(e)))
            return None
 
    def revision(self):
        """
        @rtype int
        @return the revision number. if not already set, it is initialized to 1.
        """
        rev = self.getProperty(elements.Revision)
        if rev is None:
            return 1
        else:
            return int(str(rev))

    def isEncrypted(self):
        """
        @rtype boolean
        @return whether the file is encrypted. 
        """
        isEncrypted = self.getProperty(elements.Encrypted)
        return int(str(isEncrypted)) == 1

    def contentSignature(self):
        """
        @return: the checksum of the resource content
        """
        return str(self.getProperty(elements.ContentSignature))
    
    def metaDataSignature(self):
        """
        @return the signature of the signed metadata
        """
        return str(self.getProperty(elements.MetaDataSignature))


    def _dataIsCorrect(self):
        cs = self.contentSignature()
        if cs == self._computeContentHexDigest():
            log.debug("data signature for resource '%s' is correct: %s", self.resourceID(), cs)
            return True
        else:
            log.info("data signature for resource '%s' is incorrect: %s", self.resourceID(), cs)
            return False

    def _metaDataIsCorrect(self):

        publicKey = ezKey()
        publicKey.importKey(self.publicKeyString())
        
        sm = self.signableMetadata()
        ms = self.metaDataSignature()
        
        #log.debug(ms)
        #log.debug(sm)
        try:
            isCorrect = publicKey.verifyString(sm, ms)
            if not isCorrect:
                log.info("Incorrect meta data for: %r", self.resourceID())
                log.info("Meta data to be signed: %r", self.signableMetadata())
                return False
            else:
                return True
        except Exception, e:
            log.debug("TODO more specific error handling needed here", exc_info = e)
            log.info("Can not verify metadata %s against signature %s", sm, ms, exc_info = e)
            return False
    
    def validate(self):
        return (self._dataIsCorrect() and self._metaDataIsCorrect())

    def _computeContentHexDigest(self):
        """
        @return hexdigest for content of self
        """
        hashObj = util.getHashObject()
        callbacks = [ hashObj.update ]
        f = self.open()
        BUFSIZE = LOCAL_BUFSIZE # files and StringIO
        # This is sort of hacky thanx to duck typing.
        # What we want to achieve here is rate limiting for network based activity.
        if f.__class__.__name__ == 'StringIO':
            size = len(f.getvalue()) # this is ok because we should only hit StringIO for directories which are only 9 bytes
        elif f.__class__.__name__ == 'HTTPResponse':
            size = long(f.getheader('Content-Length'))
            callbacks.append(RateLimit(size, MAX_DOWNLOAD_SPEED))
            BUFSIZE = HTTP_BUFSIZE
            log.debug("downloading clone %r to compute a digest (size %d)", self, size)
        elif f.__class__.__name__ == 'file':
            size = os.fstat(f.fileno())[stat.ST_SIZE]
        else:
            raise Exception, "resource %s has unknown size" % repr(self)
        bytesread = bufferedReadLoop(f.read, BUFSIZE, size, callbacks)
        assert bytesread == size, "Expected size of resource does not match the number of bytes read!"
        f.close()
        return hashObj.hexdigest()

    def resourceID(self):
        """
        @see IResource
        """ 
        return self.getProperty(elements.ResourceID)
    
    def exists(self):
        """
        @rtype boolean
        @return true, if the corresponding file exists. If the resource is not the root resource, it must additionally be
            referenced by the parent collection.
        """   
        raise NotImplementedError
    
    def children(self):
        raise NotImplementedError

    def clones(self):
        """
        Return the list of clones stored with this resource.
        
        Note that this will recursively initialize the clone field all parent resources, 
        until one parent is found that does have clones. Will raise a RuntimeError if the root node has no
        clones.
        
        @see propertyManager.inheritClones
        """
        from angel_app.resource.remote import clone
        clonesElement = self.getProperty(elements.Clones)
        if clonesElement is None:
            return []
        else:
            return clone.clonesFromElement(clonesElement)

    def childLinks(self):
        return self.getProperty(elements.Children)


    def publicKeyString(self):
        """
        @return: the string representation of the resource's public key.
        """
        return str(self.getProperty(elements.PublicKeyString))
 
    def keyUUID(self):
        """
        @return a UUID of the first 32 bytes of the SHA checksum of the resource's public key string.
        """
        return util.uuidFromPublicKeyString(self.publicKeyString())

    def signableMetadata(self):
        """
        Returns a string representation of the metadata that needs to
        be signed.
        """
        return "".join([self.getProperty(key).toxml() for key in elements.signedKeys])
