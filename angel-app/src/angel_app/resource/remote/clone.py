from httplib import HTTPConnection
import urlparse

from twisted.web2 import responsecode
from twisted.web2.dav import davxml
from twisted.web2.dav.element import rfc2518
from zope.interface import implements

from angel_app import elements
from angel_app.config import config
from angel_app.log import getLogger
from angel_app.resource import IResource
from angel_app.resource.remote.httpRemote import HTTPRemote
from angel_app.resource.resource import Resource
from angel_app.resource.remote.propertyManager import PropertyManager

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

class Clone(Resource):
    """
    Provides methods for transparent access to frequently used clone meta data.
    """
    implements(IResource.IAngelResource)
    
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
        
        self.updateRemote(HTTPRemote(self.host, self.port, self.path))
       
    def getPropertyManager(self):
        return self.propertyManager
    
    def updateRemote(self, remote):
        self.remote = remote
        self.propertyManager = PropertyManager(remote)
     
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
        
    
    def checkForRedirect(self):

        response = self.remote.performRequest(method = "HEAD", body = "")
        if response.status == responsecode.MOVED_PERMANENTLY:
            log.info("clone received redirect: " + `self`)
            try:
                redirectURL = urlparse.urlparse(response.getheader("location"))
                path = redirectURL[2]
                assert path != ""
                self.path = path
                self.updateRemote(HTTPRemote(self.host, self.port, self.path))
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
  
    def stream(self):
        response = self.remote.performRequest()
        if response.status != responsecode.OK:
            raise "must receive an OK response for GET, otherwise something's wrong"
        return response
    

    def exists(self): 
        """
        Keep in mind that existence does not imply validity.
        """
        try:
            response = self.remote.performRequest(method = "HEAD", body = "")
            return response.status == responsecode.OK
        except:
            return False       

    
    def ping(self):
        """
        @return whether the remote host is reachable
        """
        try:
            dummyresponse = self.remote.performRequestWithTimeOut()
            return True
        except:
            return False  
     
    def findChildren(self):
         raise NotImplementedError    

        
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
    