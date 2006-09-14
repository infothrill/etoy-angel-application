"""
WebDAV LOCK method


Provides minimalistic LOCK request support required to be WebDAV Level 2 compliant.

Only exclusive (see L{assertExclusiveLock}) write (see L{assertWriteLock}) locks are supported.
Timeout headers are ignored (RFC 2518, Section 9.8).
"""

__all__ = ["http_LOCK"]

from twisted.python import log
from twisted.internet.defer import deferredGenerator
from twisted.internet.defer import waitForDeferred
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse
from twisted.web2.dav.http import MultiStatusResponse
from twisted.web2.dav import davxml
from twisted.web2.dav.util import davXMLFromStream
from twisted.web2.dav.element.rfc2518 import LockInfo

from angel_app.contrib.uuid import uuid4



def parseLockRequest(stream):
    """
    @return a twisted.web2.dav.element.WebDAVElement corresponding to the root element of the request body.
    
    Raises an error if the root element is not a lockinfo element, or 
    if the request body (the stream) is empty. The latter is not quite
    correct, since according to RFC 2518, Section 7.8, a client may submit a LOCK request
    with an empty body (and an appropriate If: header) in order to refresh a lock, but it 
    should be good enough for now.
    """

    # obtain a DOM representation of the xml on the stream
    document = waitForDeferred(davXMLFromStream(stream))
    yield document
    document = document.getResult()
   
    if document is None:
        # No request body makes no sense.
        # this is actually not quite correct, 
        error = "Empty LOCK request."
        log.err(error)
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error)) 
   
    if not isinstance(document.root_element, LockInfo):
        error = "LOCK request must have lockinfo element as root element."
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
    
    yield document.root_element



def assertExclusiveLock(lockInfo):
    """
    RFC 2518, Section 15.2: A class 2 compliant resource MUST meet all class 1 requirements and support the 
    LOCK method, the supportedlock property, the lockdiscovery property, the Time-Out response header and the 
    Lock-Token request header. A class "2" compliant resource SHOULD also support the Time-Out request header 
    and the owner XML element.
    
    RFC 2518, Section 6.1: If the server does support locking it may choose to support any combination of 
    exclusive and shared locks for any access types. 
    
    
    In other words, it seems sufficient to only support exclusive locks in order to be class 2 compliant,
    which is convenient.
    """
    
       
    error = "Only exclusive locks supported so far."   
    if lockInfo.childOfType(davxml.LockScope).childOfType(davxml.Exclusive) is None:
        raise HTTPError(StatusResponse(responsecode.NOT_IMPLEMENTED, error))



def assertWriteLock(lockInfo):
    """
    RFC 2518, Section 7: The write lock is a specific instance of a lock type, 
    and is the only lock type described in this specification.
    
    I suppose this means that we can require that the LOCK request requests a
    write lock.
    """  
    
    error = "Only write locks supported so far."
    if lockInfo.childOfType(davxml.LockType).childOfType(davxml.Write) is None:
        raise HTTPError(StatusResponse(responsecode.NOT_IMPLEMENTED, error))



def buildActiveLock(lockInfo, depth):
    """
    build a activelock element corresponding to the lockinfo document body and depth
    header from the request.
    
    e.g. http://www.webdav.org/specs/rfc2518.html#rfc.section.8.10.8
    """
    olt = "opaquelocktoken:" + str(uuid4())
    href = davxml.HRef.fromString(olt)
    lockToken = davxml.LockToken(href)
    
    depth = davxml.Depth(depth)
    
    activeLock = davxml.ActiveLock(
                                   lockInfo.childOfType(davxml.LockType),
                                   lockInfo.childOfType(davxml.LockScope),
                                   depth,
                                   lockInfo.childOfType(davxml.Owner),
                                   lockToken
                                   ) 
    return activeLock


def performLockOperation(filePath, lockInfo):
    
          
    yield None



def buildLockResponse(activeLock):
         #
        # TODO: Generate XML output stream (do something with lock)
        #

        # vincent:
        # we should certainly return a reasonable response here
        # (for inspiration, see twisted.dav.method.propfind and RFC 2518, examples 8.10.8
        # through 8.10.10), but since i only want OS X 10.4 to be happy (and it is with
        # this), i'll stop here for now.   
    yield davxml.LockDiscovery()

def getDepth(headers):
    """
    RFC 2518, Section 8.10.4: 
    
    The Depth header may be used with the LOCK method. Values other than 0 or infinity MUST NOT be used with the 
    Depth header on a LOCK method. All resources that support the LOCK method MUST support the Depth header.
    
    If no Depth header is submitted on a LOCK request then the request MUST act as if a "Depth:infinity" had been submitted.
    """
    depth = headers.getHeader("depth", "infinity")
    
    
    if depth not in ("0", "infinity"):
        error = "Values other than 0 or infinity MUST NOT be used with the Depth header on a LOCK method."
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
    
    return depth
        
    

def processLockRequest(resource, request):
    """
    Respond to a LOCK request. (RFC 2518, section 8.10)
    
    Relevant notes:
    
    """
    
    requestStream = request.stream
    depth = getDepth(request.headers)
    
    # generate DAVDocument from request body
    lockInfo = waitForDeferred(deferredGenerator(parseLockRequest)(requestStream))
    yield lockInfo
    lockInfo = lockInfo.getResult()
            
    assertExclusiveLock(lockInfo)   
    assertWriteLock(lockInfo)
    
    # build the corresponding activelock element
    # e.g. http://www.webdav.org/specs/rfc2518.html#rfc.section.8.10.8
    activeLock = buildActiveLock(lockInfo, depth)
    
    lockResponses = waitForDeferred(deferredGenerator(performLockOperation)(resource, activeLock))
    yield lockResponses
    lockResponses = lockResponses.getResult()

    yield MultiStatusResponse([lockResponses])

def getOpaqueLockToken(request):
    """
    @return the opaque lock token on the If:-header, if it exists.
    
    TODO: (vincent) i could not find meaningful documentation on the structure/semantics
    of the If: header (if such a thing exists). We currently assume it looks like this:
    If: (<opaquelocktoken:UUID>)
    which is certainly overly simplistic (see examples in RFC 2518). Should work for now,
    though. THIS MUST BE CLEANED UP!!!
    """
    
    if not request.headers.hasHeader("If:"): return None
    
    ifh = request.headers.getRawHeaders("If:")[0]   
    
    # ugly hack: the string representation of a UUID has 8 + 3 * 4 + 12 + 4 == 36 characters,
    # the string "opaquelocktoken" has 15 characters, plus one ":" and four padding 
    # characters this yields a string of 56 characters:
    if not len(ifh) != 56:
        error = "invalid opaque lock token"
        HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
   
    # remove the padding characters:
    oplt = ifh[2:-2]
    
    if not oplt.find("opaquelocktoken") == 0:
        error = "invalid opaque lock token"
        HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
        
    return oplt

class Lockable:
    """
    A mixin class for http resources that provide the DAVPropertyMixIn.
    """
    def preconditions_LOCK(self, request):
        """
        Throw a NOT_FOUND error if the requested file does not exist.
        """
        if not self.exists():
            error = "File not found in LOCK request: %s" % ( self.fp.path, )
            raise HTTPError(StatusResponse(responsecode.NOT_FOUND, error))
        
        if not self.isWritableFile():
            error = "No write permission for file."
            HTTPError(StatusResponse(responsecode.UNAUTHORIZED, error))
            
        if not self.__isMutable(request):
            error = "Resource is locked and you don't have the proper token handy."
            HTTPError(StatusResponse(responsecode.LOCKED, error))
    
    def http_LOCK(self, request):
        """
        Method interface to locking operation.
        """
        return deferredGenerator(processLockRequest)(self, request)
    
    def __getLock(self):
        """
        @return the activeLock WebDAVDocument stored in the attributes, if it exists, otherwise None.
        """
        if self.hasAttribute(davxml.ActiveLock):
            return self.getAttribute(davxml.ActiveLock)
        else:
            return None
        
    def __setLock(self, activeLock, request):
        """
        Lock this resource with the supplied activelock.
        """

        if not self.__isMutable(request):
            error = "Resource is locked and you don't have the proper token handy."
            HTTPError(StatusResponse(responsecode.LOCKED, error))       
        
        self.writeProperty(activeLock, request)       
    
    def __lockToken(self):
        """
        @return the uri of the opaquelocktoken of the lock on this resource, if the latter exists, otherwise None.
        
        See: http://webdav.org/specs/rfc2518.html#rfc.section.6.4
        """
        lock = self.__getLock() 
        if lock is None: return None
        return str(lock.childOfType(davxml.LockToken).childOfType(davxml.HRef))
    
    def __isMutable(self, request):
        """
        A resource is considered mutable in this context, if 
        -- it is not locked
        -- the request provides the opaquelocktoken corresponding to the lock on this resource
        """
        lt = self.__lockToken()
        if lt is None or lt == getOpaqueLockToken(request): return True
        
        return False
        
        
        
