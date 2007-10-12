from httplib import HTTPConnection
import urlparse

from twisted.web2 import responsecode
from twisted.web2.dav import davxml
from twisted.web2.dav.element import rfc2518
from zope.interface import implements

from angel_app import elements
from angel_app.config import config
from angel_app.contrib.ezPyCrypto import key
from angel_app.log import getLogger
from angel_app.resource import IResource
#from angel_app.resource.remote import util

log = getLogger(__name__)


AngelConfig = config.getConfig()
providerport = AngelConfig.getint("provider","listenPort")

class CloneError(Exception):
    def __init__(self,value):
        self.parameter=value
    def __str__(self):
        return repr(self.parameter)

class CloneNotFoundError(CloneError):
    pass

class Clone(object):
    """
    Provides methods for transparent access to frequently used clone meta data.
    """
    implements(IResource.IAngelResource)
    
    cachedProperties = elements.signedKeys + [elements.MetaDataSignature, rfc2518.ResourceType, elements.Clones]
    
    def __init__(self, host = "localhost", port = providerport, path = "/"):
        """
        @rtype Clone
        @return a new clone
        """
        
        # the host name or ip
        self.host = host
        
        # a port number
        self.port = port
        
        # a path string. must be valid as part of an absolute URL (i.e. quoted, using "/")
        self.path = path
        
        self.validatePath()
        self.validateHostPort()
        
        self.propertyCache = {}
        
    def validatePath(self):
        from urllib import url2pathname, pathname2url
        # if the path is valid, then the composition of url2pathname and pathname2url is the identity function
        if not pathname2url(url2pathname(self.path)) == self.path:
            raise CloneError("Invalid path for clone: " + `self.path`)

        if not len(self.path) > 0:
            raise CloneError("Need non-empty path for clone. Got: " + self.path)
        
        if not self.path[0] == "/":
            raise CloneError("Need absolute path for clone. Got: " + self.path)
        
    def validateHostPort(self):
        # if the clone is valid, we must be able to reconstruct the host, port, path from the string representation
        url = urlparse.urlsplit("http://" + `self`)
        if not url[1] == self.host + ":" + `self.port`:
            raise CloneError("Invalid host for clone: " + `self`)
        # as of python 2.5, we will also be able to do this:
        # assert url.port == self.port                         
        
    def __updateCache(self):
        """
        A single PROPFIND request can request multiple properties. Use this method to update the cache
        of all properties we will likely need.
        """
        properties = okProperties(self._propertiesDocument(self.cachedProperties))
        for property in properties:
            self.propertyCache[property.qname()] = property                            
        
    
    def checkForRedirect(self):

        response = self._performRequest(method = "HEAD", body = "")
        if response.status == responsecode.MOVED_PERMANENTLY:
            log.info("clone received redirect: " + `self`)
            try:
                redirectURL = urlparse.urlparse(response.getheader("location"))
                path = redirectURL[2]
                assert path != ""
                self.path = path
                log.info("redirecting to: " + `path`)
            except:
                error = "redirection url invalid: " + `redirectURL`
                log.warn(error)
                raise CloneNotFoundError(error)
            
    
    def __eq__(self, clone):
        """
        @rtype boolean
        Comparison operator.
        """
        return self.host == clone.host and self.port == clone.port
    
    def __repr__(self):
        return self.host + ":" + `self.port` + self.path
    
    def __hash__(self):
        return `self`.__hash__()
    
    def _performRequestWithTimeOut(self, method = "CONNECT", headers = {}, body = "", timeout = 3.0):
        """
        Perform a request with a timeout. 
        
        TODO: It would be nice if we could set timeouts on a per-socket basis. For the time being, it
        seems we have to operate with socket.setdefaulttimeout(), which is obviously a dangerous and
        annoying hack (since it applies to all future sockets). We need to make sure that in the end, 
        the default time out is set back to the original value (typpically None). Since python2.4 does
        not yet support the finally clause, we have to do that in two places (i.e. in the try statement,
        if the request succeeds, in the catch statement otherwise).
        
        @see Clone.ping
        """
        
        import socket
        conn = HTTPConnection(self.host, self.port)
        oldTimeOut = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            conn.connect()
            conn.request(
                 method, 
                 self.path,
                 headers = headers,
                 body = body
                 )
            # revert back to blocking sockets -- 
            socket.setdefaulttimeout(oldTimeOut)
            return conn.getresponse()
        except:
            # revert back to blocking sockets
            socket.setdefaulttimeout(oldTimeOut)
            # then re-raise the exception
            raise


    def _performRequest(self, method = "GET", headers = {}, body = ""):
        """
        Perform an http request on the clone's host.
        
        TODO: add content-length headers
        
        TODO: add support for stream bodies.
        
        vinc: I'm not sure the urllib client supports stream arguments for the body. In either case, _performRequest
        is not only called for file pushing, but is a generic abstraction for any http request to the given host
        (HEAD, PROPFIND, GET, MKCOL, PROPPATCH). One might have to distinguish between string-type bodies such as used
        for the PROPFIND and PROPPATCH requests and stream type bodies. In either case, it seems possible and
        desirable to supply a "content-length" header.

        pol: - httplib does NOT support stream bodies (as in python <=2.5)
             - httplib does add the content-length header automatically (as of python >=2.4)
             - urllib/urllib2 have similar problems (they rely on httlib), although
               urllib2's design allows for extensions, so it could be
               hooked in, but this would essentially mean writing our
               own request() method (not relying on httplib) and going
               down the rabbit hole on urlencoding/multipart mime content encoding etc.
        """
        conn = HTTPConnection(self.host, self.port)
        headers["content-length"] = str(len(body))
        conn.connect() 

        conn.request(
                 method, 
                 self.path,
                 headers = headers,
                 body = body
                 )
        
        return conn.getresponse()

  
    def stream(self):
        response = self._performRequest()
        if response.status != responsecode.OK:
            raise "must receive an OK response for GET, otherwise something's wrong"
        return response
    
    
    def _propertiesDocument(self, properties):
        """
        Perform a PROPFIND request on the clone, returning the response body as an xml document.
        DO NOT use this directly. Use getProperties instead.
        
        @rtype string
        @return the raw XML body of the multistatus response corresponding to the respective PROPFIND request.
        """  
        resp = self._performRequest(
                              method = "PROPFIND", 
                              headers = {"Depth" : 0}, 
                              body = makePropfindRequestBody(properties)
                              )

        if resp.status != responsecode.MULTI_STATUS:
            if resp.status == responsecode.NOT_FOUND:
                raise CloneNotFoundError("Clone %s not found, response code is: %s" % (self, `resp.status`))
            else:
                raise CloneError("must receive a MULTI_STATUS response for PROPFIND, otherwise something's wrong, got: " + `resp.status`)


        return davxml.WebDAVDocument.fromString(resp.read())
    
    def _getProperties(self, properties):
        """
        Perform a PROPPFIND request on the clone, asserting a successful query for all properties.
        Add all returned properties to the cache.
        
        @param a list of property xml elements.
        @return a davxml.PropertyContainer element containing the requested properties
        """
        propertyDoc = self._propertiesDocument(properties)
        
        okp =  okProperties(propertyDoc)
        
        # cache the properties for later re-use    
        for pp in okp.children:
            self.propertyCache[pp.qname()] = pp 
            
        return okp
    
    def getProperties(self, properties):
        """
        Same as _getProperties, but with a cache lookup step in between.
        
        @return a davxml.PropertyContainer
        @see _getProperties
        """
        
        # check if one of the requested properties is not in the cache
        allCached = True
        for pp in properties:
            if pp.qname() not in self.propertyCache.keys():
                allCached = False
                break
            
        if not allCached:
            # since we need to make a request anyway, we 
            # might as well request frequently needed elements -- but avoid duplicates
            rp = self.cachedProperties + [pp for pp in properties if pp not in self.cachedProperties]
            returned = self._getProperties(rp)
        else:
            props = [self.propertyCache[p.qname()] for p in properties]       
            returned = davxml.PropertyContainer(*props)
            
        return returned
        
    def getProperty(self, property):
        """
        Quite like getProperties, but for a single property only. In contrast to
        getProperties, it doesn't return a davxml.PropertyContainer, but an element
        of the same type as the argument element.
        
        @return the property with a value
        """
        return self.getProperties([property]).childOfType(property)
    

    def exists(self): 
        """
        Keep in mind that existence does not imply validity.
        """
        try:
            response = self._performRequest(method = "HEAD", body = "")
            return response.status == responsecode.OK
        except:
            return False       

    
    def ping(self):
        """
        @return whether the remote host is reachable
        """
        try:
            dummyresponse = self._performRequestWithTimeOut()
            return True
        except:
            return False  

    def isCollection(self):
         return self.getProperty(rfc2518.ResourceType) == rfc2518.Collection.sname()
    
    
    def resourceID(self):
        return str(self.getProperty(elements.ResourceID))
    
    
    def revision(self):
        """
        @rtype int
        @return the clone's revision number.
        """
        try:
            return int(str(self.getProperty(elements.Revision)))
        except:
            log.warn("no revision found on clone: " + `self`)
            return -1
    
    def publicKeyString(self):
        """
        @rtype string
        @return the public key string of the clone.
        """
        return str(self.getProperty(elements.PublicKeyString))
    
    def metaDataSignature(self):
        """
        @rtype string
        @return the public key string of the clone.
        """
        signature = str(self.getProperty(elements.MetaDataSignature))
        return signature
    
    
    def validate(self):
        """
        @rtype boolean
        @return if the meta data of a given clone is internally consistent.
        """
        
        
        toBeVerified = "".join([
                                self.getProperty(element).toxml()
                                for element in elements.signedKeys
                                ])
        
        pubKey = key()
        try:
            pubKey.importKey(self.publicKeyString())
            return pubKey.verifyString(
                                   toBeVerified, 
                                   self.metaDataSignature())
            
        except Exception, e:
            log.warn(`self` + ": validation failed. Exception: " + `e`)
            return False
        
        
        
    def cloneList(self):
        """
        @rtype [(string, int)]
        @return a list of (string hostname, int port) tuples of clones registered with this clone.
        """

        try:
            prop = self.getProperty(elements.Clones)
                                       
            return clonesFromElement(prop)
        except:
            return []
   
def makePropfindRequestBody(properties):
    """
    @rtype string
    @return XML body of PROPFIND request.
    """
    return rfc2518.PropertyFind(
                rfc2518.PropertyContainer(
                      *[property() for property in properties]
                      )).toxml()
                      
def propertiesFromPropfindResponse(response):
    """
    Unwrap the actual property elements from a PROPFIND response.
    
    @param response: a MULTISTATUS response element
    
    @return a pair of lists of xml element objects. the first entry contains the properties for which the
    request succeeded, the second pair contains those for which it failed.
    
    @see twisted.web2.dav.method.propfind
    """
    
    responses = response.root_element.childrenOfType(davxml.PropertyStatusResponse)
    assert 1 == len(responses), "We only do depth = 0 queries, so must receive responses for exactly 1 url."
    response = responses[0]

    # get the url
    url = response.childOfType(davxml.HRef).children[0]
    # TODO: this should in fact be the clone's self.path, we could check this, too
    
    propstats = response.childrenOfType(davxml.PropertyStatus)
    
    propertiesByResponseCode = {}
    
    for ps in propstats:
        status = ps.childOfType(davxml.Status)    
        responseCode = int(str(status).split()[1])
        # TODO: we should test that this is indeed a valid response code
        prop = ps.childOfType(davxml.PropertyContainer)
        propertiesByResponseCode[responseCode] = prop
        
    return propertiesByResponseCode

def okProperties(response):
    """
    In addition to the validation carrid out by propertiesFromPropfindResponse,    
    assert that the request succeeded for all requested properties. Raise a KeyError otherwise.
    
    @param the response body
    @return: a davxml.PropertyContainer of all properties for which the request succeeded.
    
    @see propertiesFromPropfindResponse
    """
    
    propertiesByResponseCode = propertiesFromPropfindResponse(response)
    
    if propertiesByResponseCode.keys() != [responsecode.OK]:
        notOKCodes = [kk for kk in propertiesByResponseCode.keys() if kk != responsecode.OK]
        notOKResponses = [propertiesByResponseCode[kk] for kk in notOKCodes]
        errorProperties = "\n".join([rr.toxml() for rr in notOKResponses])
        raise KeyError, "Property requests failed for: " + errorProperties
    
    # no requests failed, return the OK responses
    return propertiesByResponseCode[responsecode.OK]
                        
        


def makeCloneBody(localResource):
    """
    Make a PROPPATCH body from the local clone for registration with a remote node.
    """
    cc = Clone("localhost", providerport, localResource.relativeURL())
    cloneElement = elements.Clone(rfc2518.HRef(`cc`))
    clonesElement = elements.Clones(*[cloneElement])
    setElement = rfc2518.Set(rfc2518.PropertyContainer(clonesElement))
    propertyUpdateElement = rfc2518.PropertyUpdate(setElement)
    return propertyUpdateElement.toxml()

def getClonesOf(clonesList):
    """
    TODO: this should probably be replaced by a generator
    
    @type clonesList [Clone]
    @param clonesList list of clones we want to get the clones from
    @rtype [Clone]
    @return list of clones of the clones in clonesList, except the clones stored on the localhost
    """
    cc = []
    for clone in clonesList:
        cc += [Clone(host, port) for host, port in clone.cloneList()]
    return cc

def getUncheckedClones(clonesList, checkedClones):
    """
    @rtype ([Clone], [Clone])
    @return (cc, checkedClones + cc), where cc ist the list of clones in clonesList which are not in checkedClones
    """
    cc = [clone for clone in clonesList if clone not in checkedClones]
    return cc, checkedClones + cc


def getMostCurrentClones(clonesList):
    """
    @rtype [Clone]
    @return the most current clones from the clonesList
    """
    newest = max([clone.revision() for clone in clonesList])    
    return [clone for clone in clonesList if clone.revision() == newest]


def splitParse(cloneUri):
    """
    DEPRECATED. This method is EVIL. Look for better alternative.
    
    @return the triple (host, port, path), where host is hostname or IP, 
    port is a port number, and path is a URL-encoded path name. Path may be the empty string.
    """
    host, rest = cloneUri.split(":")
    fragments = rest.split("/")
    port = int(fragments[0])
    
    if 1 == len(fragments):
        return (host, port, "")
    
    pathSegments = fragments[1:]
    return (host, port, "/" + "/".join(pathSegments))

def cloneFromGunk(gunk):
    assert len(gunk) > 1
    assert len(gunk) < 4
    if len(gunk) == 2: 
        return Clone(gunk[0], gunk[1])
    else:
        return Clone(gunk[0], gunk[1], gunk[2])
    
    
def cloneFromElement(cc):
    """
    Takes a child element of the Clones element and returns a Clone instance.
    """
    return cloneFromGunk(splitParse(str(cc.children[0].children[0])))


def clonesFromElement(cloneElement):
    """
    @param cloneElement a Clones element 
    @return a list of corresponding Clone instances
    """
    return [cloneFromElement(cc) for cc in cloneElement.children]

def clonesToElement(cloneList):
    """
    Takes a list of clones and generates a Clones element from it.
    """
    return elements.Clones(*[
                    elements.Clone(rfc2518.HRef(`cc`)) for cc in cloneList
                    ])
    