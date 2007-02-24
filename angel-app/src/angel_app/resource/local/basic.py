from twisted.web2 import responsecode, dirlist
from twisted.web2.http import HTTPError
from twisted.web2 import http, stream
from twisted.web2.dav.xattrprops import xattrPropertyStore
from twisted.web2.dav.element import rfc2518
from twisted.web2.dav import davxml
from angel_app import elements

from zope.interface import implements
from angel_app.resource import IResource
from angel_app.resource.local.safe import Safe
from angel_app.resource.local.external.methods.proppatch import ProppatchMixin
from angel_app.resource.local.resourceMixins import deleteable
from angel_app.log import getLogger
from angel_app.contrib import uuid
from angel_app.contrib.ezPyCrypto import key as ezKey
import os
import sha
import urllib

from angel_app.contrib import uuid

log = getLogger()

DEBUG = False

# get config:
from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")

class Basic(deleteable.Deletable, Safe):
    """
    An extension to Safe, that implements common metadata operations.
    """
    implements(IResource.IAngelResource)
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        Safe.__init__(self, path, defaultType, indexNames)
        self._dead_properties = xattrPropertyStore(self)

    def contentAsString(self):
        if self.fp.isdir(): 
            return "directory"
        return self.fp.open().read()
    
    def contentLength(self):
        if not self.isEncrypted():
            return super(Safe, self).contentLength()
        else:
            # getting the content length for an encrypted
            # file requires decryption of the file.
            # let's just pretend we don't know
            return None
 
    def get(self, davXMLTextElement):
        """
        @return the metadata element corresponding to davXMLTextElement
        """
        if not self.fp.exists():
            DEBUG and log.debug("Basic.get(): file not found for path: " + self.fp.path)
            raise HTTPError(responsecode.NOT_FOUND)
        
        # TODO: for some reason, the xml document parser wants to split
        # PCDATA strings at newlines etc., returning a list of PCDATA elements
        # rather than just one. We only have tags of depth one anyway, so we
        # might as well work around this thing right here:
        return "".join([
                        str(child) for child in 
                       self.deadProperties().get(davXMLTextElement.qname()).children
                                                 ])
        
    def getXml(self, davXMLTextElement):
        """
        @return the metadata element corresponding to davXMLTextElement
        """
        if not self.fp.exists():
            DEBUG and log.debug("AngelFile.getOrSet: file not found for path: " + self.fp.path)
            raise HTTPError(responsecode.NOT_FOUND)
        
        # TODO: for some reason, the xml document parser wants to split
        # PCDATA strings at newlines etc., returning a list of PCDATA elements
        # rather than just one. We only have tags of depth one anyway, so we
        # might as well work around this thing right here:
        return  self.deadProperties().get(davXMLTextElement.qname()).toxml()
        
    def getOrSet(self, davXmlTextElement, defaultValueString = ""):
        """
        the metadata element corresponding to davXMLTextElement, setting it to defaultValueString if not already present
        """
        try:
            return self.get(davXmlTextElement)
        
        except HTTPError:
            DEBUG and log.debug("angelFile.Basic.getOrSet: initializing element " + `davXmlTextElement.qname()` + " to " + defaultValueString)
            self.deadProperties().set(davXmlTextElement.fromString(defaultValueString))
            self.fp.restat()
            return defaultValueString
       
    def revisionNumber(self):
        """
        @rtype int
        @return the revision number. if not already set, it is initialized to 1.
        """
        return int(self.getOrSet(elements.Revision, "1"))

    def isEncrypted(self):
        """
        @rtype boolean
        @return whether the file is encrypted. 
        """
        return int(self.get(elements.Encrypted)) == 1
    
    def isWriteable(self):
        """
        A basic AngelFile is writeable (by a non-local host) exactly if:
          -- the resource is corrupted, i.e. it does not verify()
          -- the resource does not exist but is referenced by its parent()
          
        @rtype boolean
        @return whether the basic AngelFile is writeable
        """
        if not self.verify():
            DEBUG and log.debug(self.fp.path + " is writable")
            return True
        
        pp = self.parent()
        if not self.exists() and pp.verify() and [self in pp.metaDataChildren()]: 
            DEBUG and log.debug(self.fp.path + " is writable")
            return True
        
        DEBUG and log.debug(self.fp.path + " is not writable")
        return False
    
    def verify(self):
        
        if not self.exists():
            DEBUG and log.debug("Basic.verify(): False, file does not exist")
            return False
        
        try:
            pk = self.get(elements.PublicKeyString)
            cs = self.get(elements.ContentSignature)
            sm = self.signableMetadata()
            ms = self.get(elements.MetaDataSignature)
        except:
            DEBUG and log.debug("Basic.verify(): False, invalid metadata")
            return False
        
        publicKey = ezKey()
        publicKey.importKey(pk)

        dataIsCorrect = publicKey.verifyString(self.contentAsString(), cs)
        DEBUG and log.debug("data signature for file " + self.fp.path + " is correct: " + `dataIsCorrect`)
        
        DEBUG and log.debug(ms)
        DEBUG and log.debug(sm)
        metaDataIsCorrect = publicKey.verifyString(sm, ms)
        
        DEBUG and log.debug("meta data signature for file " + self.fp.path + " is correct: " + `metaDataIsCorrect`)
            
        return dataIsCorrect and metaDataIsCorrect
    
    def resourceID(self):
        """
        @see IResource
        """ 
        return self.deadProperties().get(elements.ResourceID.qname())
    
    def resourceName(self):
        """
        @return the "file name" of the resource
        """
        return self.relativePath().split(os.sep)[-1]
    
    def referenced(self):
        # the root is always referenced
        if self.parent() is None: return True
        
        return self in self.parent().metaDataChildren()
    
    def exists(self):
        """
        @rtype boolean
        @return true, if the corresponding file exists and is referenced by the parent collection.
        """       
        return self.referenced() and self.fp.exists()

    def removeIfUnreferenced(self):
        """
        @rtype boolean
        @return true if the resource was deleted, false otherwise
        """
        if self.fp.exists() and not self.exists():
            DEBUG and log.debug(self.fp.path + " not referenced by parent, deleting")
            self._recursiveDelete(self.fp.path)
            return True
        
        return False
    
    def familyPlanning(self):
        """
        Remove all direct children that are not referenced.
        """
        self.findChildren("1")

    def findChildren(self, depth):
        """ 
        @rtype [Filepath]
        @return child nodes of this node. Optionally (and by default),
        child nodes which have the deleted flag set can be ignored.
        """
        
        children = super(Basic, self).findChildren(depth)

        return [
                cc for 
                cc in children
                if not cc[0].removeIfUnreferenced()
                ]

    def relativePath(self):
        return self.fp.path.split(repository)[1]

    def parent(self):
        """
        @return this resource's parent
        """
        assert(self.fp.path.find(repository)) == 0, "Path (%s) lies outside of repository." % self.fp.path
        
        if self.fp.path == repository:
            # this is the root directory, don't return a parent
            return None
        
        return self.createSimilarFile( 
                                  self.fp.parent().path
                                  )

    def clones(self):
        """
        Return the list of clones stored with this resource.
        """
        return self.deadProperties().get(elements.Clones.qname())

    def metaDataChildren(self):
        """
        The children of this resource as specified in the resource metadata.
        This may (under special circumstances) be different from the list
        of children as specified in the findChildren routine, since the former
        lists all children as found on the file system, while the latter lists
        all children registered with the angel app. In the case of an incomplete
        push update, the latter list contains children that are not present in
        the former.
        
        TODO: this needs some more work... href parsing, validation etc.
        
        @see isWritable
        @rtype [Basic] 
        @return The children of this resource as specified in the resource metadata.
        """
        DEBUG and log.debug("Basic.metaDataChildren")
        if not self.isCollection(): return []
        
        children = self.deadProperties().get(elements.Children.qname()).children

        #validatedChildren = []
        #for child in children:
        #    sf = self.createSimilarFile(self.fp.path + os.sep + urllib.unquote(str(child.childOfType(davxml.HRef))))
        #    if sf.fp.exists(): # and str(sf.keyUUID()) == str(child.childOfType(elements.UUID).children[0]):
        #        validatedChildren.append(sf)
            
        #return validatedChildren
        return [self.createSimilarFile(self.fp.path + os.sep + urllib.unquote(str(child.childOfType(davxml.HRef))))
                for child in children]


    def publicKeyString(self):
        
        DEBUG and log.debug("retrieving public key string for: " + self.fp.path)
        
        try:
            return self.get(elements.PublicKeyString)           
        except:
            # no key set yet -- maybe we have a key handy for signing?
            try:
                keyString = self.secretKey.exportKey()
                DEBUG and log.debug("initializing public key to: " + keyString)
                return self.getOrSet(elements.PublicKeyString, keyString) 
            finally:
                raise HTTPError(responsecode.FORBIDDEN, 
                                "You don't have sufficient privileges to initialize unititialized resource " + self.relativePath())
 
    def keyUUID(self):
        """
        @return a SHA checksum of the public key string. We only take the first 16 bytes to be convertible
        to a UUID>
        """
        return uuid.UUID(
                         sha.new(
                                 self.publicKeyString()
                         ).hexdigest()[:32])

    def signableMetadata(self):
        """
        Returns a string representation of the metadata that needs to
        be signed.
        """
        try:
            sm = "".join([self.getXml(key) for key in elements.signedKeys])
            DEBUG and log.debug("signable meta data for " + self.fp.path + ":" + sm)
            return sm
        except Exception, e:
            log.error("Basic: invalid meta data: " + `e`)
            raise ValueError

    def render(self, req):
        """You know what you doing. override render method (for GET) in twisted.web2.static.py"""
        if not self.exists():
            return responsecode.NOT_FOUND

        if self.fp.isdir():
            return self.renderDirectory(req)

        return self.renderFile()

    def renderDirectory(self, req):
        if req.uri[-1] != "/":
            # Redirect to include trailing '/' in URI
            DEBUG and log.debug("redirecting")
            return http.RedirectResponse(req.unparseURL(path=req.path+'/'))
        
        # is there an index file?
        ifp = self.fp.childSearchPreauth(*self.indexNames)
        if ifp:
            # render from the index file
            return self.createSimilarFile(ifp.path).render(req)
        
        # no index file, list the directory
        return dirlist.DirectoryLister(
                    self.fp.path,
                    self.listChildren(),
                    self.contentTypes,
                    self.contentEncodings,
                    self.defaultType
                ).render(req)

    def getResponse(self):
        """
        Set up a response to a GET request.
        """
        response = http.Response()         
        
        for (header, value) in (
            ("content-type", self.contentType()),
            ("content-encoding", self.contentEncoding()),
        ):
            if value is not None:
                response.headers.setHeader(header, value)
                
        return response
    
    def getResponseStream(self):        
        """
        The Basic AngelFile just returns the cypthertext of the file.
        """
        try:
            f = self.fp.open()
        except IOError, e:
            import errno
            if e[0] == errno.EACCES:
                raise HTTPError(responsecode.FORBIDDEN)
            elif e[0] == errno.ENOENT:
                raise HTTPError(responsecode.NOT_FOUND)
            else:
                raise
        
        return stream.FileStream(f, 0, self.fp.getsize())

    def renderFile(self):
        
        DEBUG and log.debug("running renderFile")
        
        response = self.getResponse()
        response.stream = self.getResponseStream()
        DEBUG and log.debug("done running renderFile")
        return response
