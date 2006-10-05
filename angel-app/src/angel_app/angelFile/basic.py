from twisted.web2.dav.static import DAVFile
from twisted.python import log
from twisted.web2 import responsecode, dirlist
from twisted.web2.http import HTTPError
from twisted.web2 import http, stream
from twisted.web2.dav.xattrprops import xattrPropertyStore
from angel_app import elements
from angel_app.davMethods.lock import Lockable

DEBUG = False

class Basic(DAVFile):
    """
    This is a basic AngelFile that provides (at least as stubs) the necessary
    WebDAV methods, as well as support for the encryption and metadata semantics
    required by the angel-app. This class serves as the main class for the 
    angel/distributer.

    the following (destructive) DAV-methods are explicitly forbidden a priori: 
    PUT, MKCOL, DELETE, COPY, MOVE, PROPPATCH.
    we pretend to implement the following (but ignore them):
    LOCK, UNLOCK.
    the following methods are supported (directly from DAVFile):
    PROPFIND, GET
    </p>
    <p>
    See subclasses and angel_app.angelMixins for the implementation of
    specific WebDAV methods.
    </p>
    """
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        DAVFile.__init__(self, path, defaultType, indexNames)
        self._dead_properties = xattrPropertyStore(self)
        
    def http_PUT(self, request):
        """
        Disallowed.
        """
        log.err("Denying PUT request.")
        return responsecode.FORBIDDEN

    def http_MKCOL(self, request):
        """
        Disallowed.
        """
        log.err("Denying MKCOL request.")
        return responsecode.FORBIDDEN
    
    def http_DELETE(self, request):
        """
        Disallowed.
        """
        log.err("Denying DELETE request.")
        return responsecode.FORBIDDEN

    def http_COPY(self, request):
        """
        Disallowed.
        """
        log.err("Denying COPY request.")
        return responsecode.FORBIDDEN

    def http_MOVE(self, request):
        """
        Disallowed.
        """
        log.err("Denying MOVE request.")
        return responsecode.FORBIDDEN  
    
    #def http_PROPPATCH(self, request):
    #    """
    #    Disallowed.
    #    """
    #    log.err("Denying PROPPATCH request.")
    #    return responsecode.FORBIDDEN  

    def davComplianceClasses(self):
        """
        We fake level 2 compliance, to be able to run with OS X 10.4 's 
        builtin dav client. Adding locking via xattr should be relatively
        straightforward, though.
        """
        return ("1", "2") # Add "2" when we have locking

    def contentAsString(self):
        if self.fp.isdir(): 
            return "directory"
        return self.fp.open().read()
 
    def get(self, davXMLTextElement):
        
        if not self.fp.exists():
            DEBUG and log.err("AngelFile.getOrSet: file not found for path: " + self.fp.path)
            raise HTTPError(responsecode.NOT_FOUND)
        
        # TODO: for some reason, the xml document parser wants to split
        # PCDATA strings at newlines etc., returning a list of PCDATA elements
        # rather than just one. We only have tags of depth one anyway, so we
        # might as well work around this thing right here:
        return "".join([
                        str(child) for child in 
                       self.deadProperties().get(davXMLTextElement.qname()).children
                                                 ])
        
    def getOrSet(self, davXmlTextElement, defaultValueString = ""):
        
        try:
            return self.get(davXmlTextElement)
        
        except HTTPError:
            DEBUG and log.err("angelFile.Basic.getOrSet: initializing element " + `davXmlTextElement.qname()` + " to " + defaultValueString)
            self.deadProperties().set(davXmlTextElement.fromString(defaultValueString))
            self.fp.restat()
            return defaultValueString
       
    def revisionNumber(self):
        """
        @rtype int
        @return the revision number. if not already set, it is initialized to 1.
        """
        return int(self.getOrSet(elements.Revision, "1"))
    
    def isDeleted(self):
        """        
        @rtype boolean
        @return whether the deleted flag is set
        """
        vv = self.getOrSet(elements.Deleted, "0")
        id = (vv != "0")       
        DEBUG and log.err("AngelFile.isDeleted(): " + vv + ": " + `id` + " for " + self.fp.path)
        return vv != "0"
    
    def exists(self):
        """
        @rtype boolean
        @return true, if the corresponding file exists and is not flagged as deleted, false otherwise.
        """
        return self.fp.exists() and not self.isDeleted()

    def findChildren(self, depth, getDeleted = False):
        """        
        @rtype [Filepath]
        @return child nodes of this node. Optionally (and by default),
        child nodes which have the deleted flag set can be ignored.
        """
        
        if not self.fp.isdir(): return []
        
        from os import sep
        cc = super(Basic, self).findChildren(depth)
        
        if getDeleted: 
            return cc
        else:
            return [
                child for child in cc
                if not 
                self.createSimilarFile( 
                                          self.fp.path + sep + child[1]
                                          ).isDeleted()
                ]

    def publicKeyString(self):
        
        DEBUG and log.err("retrieving public key string for: " + self.fp.path)
        
        try:
            return self.get(elements.PublicKeyString)           
        except:
            # no key set yet -- maybe we have a key handy for signign?
            try:
                keyString = self.secretKey.exportKey()
                DEBUG and log.err("initializing public key to: " + keyString)
                return self.getOrSet(elements.PublicKeyString, keyString) 
            finally:
                raise HTTPError(responsecode.FORBIDDEN)
        

 

    def signableMetadata(self):
        """
        Returns a string representation of the metadata that needs to
        be signed.
        """
        pp = self.deadProperties()
        return "".join([
                                  `pp.get(key.qname())`
                                  for key in elements.signedKeys
                                  ])

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
            DEBUG and log.err("redirecting")
            return http.RedirectResponse(req.unparseURL(path=req.path+'/'))
        else:
            ifp = self.fp.childSearchPreauth(*self.indexNames)
            if ifp:
                # Render from the index file
                standin = self.createSimilarFile(ifp.path)
            else:
                # Render from a DirectoryLister
                standin = dirlist.DirectoryLister(
                    self.fp.path,
                    self.listChildren(),
                    self.contentTypes,
                    self.contentEncodings,
                    self.defaultType
                )
            return standin.render(req)

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
        DEBUG and log.err("rendering file in cyphertext: " + self.fp.path)
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
        
        DEBUG and log.err("running renderFile")
        
        response = self.getResponse()
        response.stream = self.getResponseStream()
        DEBUG and log.err("done running renderFile")
        return response
