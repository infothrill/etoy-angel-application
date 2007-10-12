from angel_app import elements
from angel_app.config import config
from angel_app.contrib.ezPyCrypto import key as ezKey
from angel_app.log import getLogger
from angel_app.resource import IResource
from angel_app.resource.local import util
from angel_app.resource.local.dirlist import DirectoryLister
from angel_app.resource.local.propertyManager import PropertyManager
from twisted.python.filepath import FilePath
from twisted.web2 import http, stream
from twisted.web2 import responsecode
from twisted.web2.dav import davxml
from twisted.web2.dav.element import rfc2518
from twisted.web2.dav.static import DAVFile
from twisted.web2.dav.xattrprops import xattrPropertyStore
from twisted.web2.http import HTTPError
from zope.interface import implements
import os
import urllib


log = getLogger(__name__)

# get config:
AngelConfig = config.getConfig()
repository = FilePath(AngelConfig.get("common","repository"))

REPR_DIRECTORY = "directory" #This is the string content representation of a directory

class Basic(DAVFile):
    
    implements(IResource.IAngelResource)
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        DAVFile.__init__(self, path, defaultType, indexNames)
        
        # disallow the creation of resources outside of the repository
        self.assertInRepository()
        
        self._dead_properties = PropertyManager(self)

    def contentAsString(self):
        return self.open().read()

    def open(self):
        """
        @return a stream-like object that has the read() and close() methods, to read the contents of the local resource
        """
        if self.fp.isdir():
            return util.StringReader(REPR_DIRECTORY)
        else:
            return self.fp.open()
        
    def stream(self):
        """
        alias for interface compliance.
        TODO: decide on eiter open() or stream()
        """
        return self.open()

    def contentLength(self):
        if not self.isEncrypted():
            return super(DAVFile, self).contentLength()
        else:
            # getting the content length for an encrypted
            # file requires decryption of the file.
            # let's just pretend we don't know
            return None
        
    def getProperty(self, element):
        """
        Return a resource property by element.
        """
        return self.deadProperties().get(element)
       
    def revision(self):
        """
        @rtype int
        @return the revision number. if not already set, it is initialized to 1.
        """
        return int(str(self.deadProperties().get(elements.Revision.qname())))

    def isEncrypted(self):
        """
        @rtype boolean
        @return whether the file is encrypted. 
        """
        isEncrypted = self.deadProperties().get(elements.Encrypted.qname())
        return int(str(isEncrypted)) == 1

    def contentSignature(self):
        """
        @return: the checksum of the resource content
        """
        return str(self.get(elements.ContentSignature))
    
    def metaDataSignature(self):
        """
        @return the signature of the signed metadata
        """
        return str(self.get(elements.MetaDataSignature))
    
    def verify(self):
        if not self.exists():
            log.debug("Basic.verify(): False, file does not exist")
            return False
        
        try:
            pk = self.publicKeyString()
            cs = self.contentSignature()
            sm = self.signableMetadata()
            ms = self.metaDataSignature()
        except:
            log.debug("Basic.verify(): False, invalid metadata")
            return False
        
        dataIsCorrect = False
        if cs == self._computeContentHexDigest():
            dataIsCorrect = True
            log.debug("data signature for file '%s' is correct: %s" % (self.fp.path, cs) )
        else:
            log.info("data signature for file '%s' is incorrect: %s" % (self.fp.path, cs) )
            return False
        
        publicKey = ezKey()
        publicKey.importKey(pk)
        
        log.debug(ms)
        log.debug(sm)
        try:
            metaDataIsCorrect = publicKey.verifyString(sm, ms)
        except:
            log.info("Can not verify metadata %s against signature %s" % (sm, ms))
            return False
        
        log.debug("meta data signature for file " + self.fp.path + " is correct: " + `metaDataIsCorrect`)
            
        return dataIsCorrect and metaDataIsCorrect
    
    def _computeContentHexDigest(self):
        """
        @return hexdigest for content of self
        """
        hash = util.getHashObject()
        f = self.open()
        bufsize = 4096 # 4 kB
        while True:
            buf = f.read(bufsize)
            if len(buf) == 0:
                break
            hash.update(buf)
        f.close()
        return hash.hexdigest()

    def resourceID(self):
        """
        @see IResource
        """ 
        return self.deadProperties().get(elements.ResourceID.qname())
    
    def resourceName(self):
        """
        
        @return the "file name" of the resource, return "/" for the repository root
        """
        if self.isRepositoryRoot(): 
            return os.sep
        else: 
            return self.fp.segmentsFrom(repository)[-1]
        
    def quotedResourceName(self):
        return urllib.quote(self.resourceName())
    
    def referenced(self):
        """
        Returns true if the resource is referenced by the parent resource.
        """
        return self.getChildElement() in self.parent().childLinks()
    
    def exists(self):
        """
        @rtype boolean
        @return true, if the corresponding file exists. If the resource is not the root resource, it must additionally be
            referenced by the parent collection.
        """   
        if not os.path.exists(self.fp.path): 

            return False 

        if not self.isRepositoryRoot(): 
            return self.referenced()
        else:
            return True

    def removeIfUnreferenced(self):
        """
        @rtype boolean
        @return true if the resource was deleted, false otherwise
        """
        if self.isRepositoryRoot():
            # the root is never referenced
            return False
        
        if os.path.exists(self.fp.path) and not self.exists():
            log.info(self.fp.path + " not referenced by parent, deleting")
            self._recursiveDelete(self.fp.path)
            return True
        
        # TODO: this is highly inefficient, since we do it once for every child, rather
        # than just once for the parent.
        pc = self.parent().deadProperties().get(elements.Children.qname()).children
        
        childIDs = [str(child.childOfType(elements.UUID)) for child in pc]
        
        if str(self.keyUUID()) not in childIDs:
            log.info(self.fp.path + ": invalid signature")
            log.info("did not find: " + str(self.keyUUID()) + " in " + `childIDs`)
            self._recursiveDelete(self.fp.path)
            return True
        
        return False
    
    def garbageCollect(self):
        
        self.removeIfUnreferenced()
        
        if not self.verify():
            # empty the contents of the file, but retain the file itself for the metadata
            log.info("garbage-collecting resource: " + self.fp.path)
            open(self.fp.path, "w").close() # TODO: non-atomic
    
    def familyPlanning(self):
        """
        Remove all direct children that are not (properly) referenced.
        """
        self.findChildren("1")

    def findChildren(self, depth = "0"):
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
        """
        Returns the relative path with respect to the repository root as an absolute path,
        i.e. ${repository}/foo becomes "/foo", for the repository itself, "/" is returned.
        """
        if self.isRepositoryRoot(): return os.sep
        path = os.sep + os.sep.join(self.fp.segmentsFrom(repository))
        if self.isCollection():
            path += os.sep
        return path
    
    def relativeURL(self):
        """
        @return: a URL-quoted representation of self.relativePath()
        """
        return urllib.pathname2url(self.relativePath())
    
    def insideRepository(self):
        """
        Returns true if the resource is located beneath the repository root. False otherwise.
        """
        return self.fp.path.find(repository.path) == 0
    
    def assertInRepository(self):
        assert self.insideRepository(), "Path (%s) lies outside of repository." % self.fp.path
    
    def isRepositoryRoot(self):
        """
        Returns true, if the resource is the repository's root resource, false otherwise.
        """
        return self.fp.path == repository.path

    def parent(self):
        """
        @return this resource's parent. if this resource is the repository root, return None.
        Fail, if the resource is not located inside the repository.
        """
        self.assertInRepository()
        
        if self.isRepositoryRoot():
            # this is the root directory, don't return a parent
            return None
        
        return self.createSimilarFile( 
                                  self.fp.parent().path
                                  )

    def clones(self):
        """
        Return the list of clones stored with this resource.
        
        Note that this will recursively initialize the clone field all parent resources, 
        until one parent is found that does have clones. Will raise a RuntimeError if the root node has no
        clones.
        
        @see propertyManager.inheritClones
        """
        from angel_app.resource.remote import clone
        clonesElement = self.deadProperties().get(elements.Clones.qname())
        return clone.clonesFromElement(clonesElement)

    def childLinks(self):
        return self.deadProperties().get(elements.Children.qname())

    def getChildElement(self):
        """
        @return the child element for this resource.
        """
        return elements.Child(*[
                         rfc2518.HRef(self.quotedResourceName()),
                         elements.UUID(str(self.keyUUID())),
                         self.resourceID()
                         ])

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
        log.debug("Basic.metaDataChildren for resource: " + self.fp.path)
        if not self.isCollection(): return []
        
        children = self.childLinks().children

        links = [str(child.childOfType(davxml.HRef)) for child in children]
        return [self.createSimilarFile(self.fp.path + os.sep + urllib.url2pathname(link))
                for link in links]


    def publicKeyString(self):
        """
        @return: the string representation of the resource's public key.
        """
        return str(self.deadProperties().get(elements.PublicKeyString.qname()))
 
    def keyUUID(self):
        """
        @return a SHA checksum of the public key string. We only take the first 16 bytes to be convertible
        to a UUID>
        """
        return util.uuidFromPublicKeyString(self.publicKeyString())

    def sigUUID(self):
        """
        @return a SHA checksum of the resource's signature. We only take the first 16 bytes to be convertible
        to a UUID>
        """
        return util.uuidFromPublicKeyString(self.get(elements.MetaDataSignature))

    def signableMetadata(self):
        """
        Returns a string representation of the metadata that needs to
        be signed.
        """
        try:
            sm = "".join([self.deadProperties().get(key.qname()).toxml() for key in elements.signedKeys])
            log.debug("signable meta data for " + self.fp.path + ":" + sm)
            return sm
        except Exception, e:
            log.error("Basic: invalid meta data: " + `e`)
            raise

    def render(self, req):
        """You know what you doing. override render method (for GET) in twisted.web2.static.py"""
        if not self.exists():
            return responsecode.NOT_FOUND

        if self.fp.isdir():
            return self.renderDirectory(req)
        else:
            return self.renderFile()

    def renderDirectory(self, req):
        if req.uri[-1] != "/":
            # Redirect to include trailing '/' in URI
            log.debug("redirecting")
            return http.RedirectResponse(req.unparseURL(path=req.path+'/'))
        
        # is there an index file?
        ifp = self.fp.childSearchPreauth(*self.indexNames)
        if ifp:
            # render from the index file
            return self.createSimilarFile(ifp.path).render(req)
        
        # no index file, list the directory
        return DirectoryLister(
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
        
        log.debug("running renderFile")
        
        response = self.getResponse()
        response.stream = self.getResponseStream()
        log.debug("done running renderFile")
        return response
