from angel_app import elements
from angel_app.config import config
from angel_app.log import getLogger
from angel_app.resource import IResource
from angel_app.resource.remote.contentManager import ContentManager
from angel_app.resource.remote.httpRemote import HTTPRemote
from angel_app.resource.remote.propertyManager import PropertyManager
from angel_app.resource.resource import Resource
from twisted.web2 import responsecode
from twisted.web2.dav.element import rfc2518
from zope.interface import implements
from angel_app.contrib import uriparse


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
    
    def __init__(self, host = "localhost", port = providerport, path = "/", scheme = "http"):
        """
        @rtype Clone
        @return a new clone
        """
        self.scheme = scheme
        
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
        """
        @see updateRemote
        """
        return self.propertyManager
    
    def getContentManager(self):
        return self.contentManager
    
    def updateRemote(self, remote):
        """
        Called when the remote clone address changes.
        """
        self.remote = remote
        self.propertyManager = PropertyManager(remote)
        self.contentManager = ContentManager(self)
     
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
        url = uriparse.urisplit(`self`)
        if not url[1] == self.host + ":" + `self.port`:
            raise CloneError("Invalid host for clone: " + `self`)
        # as of python 2.5, we will also be able to do this:
        # assert url.port == self.port                                                  
        
    
    def checkForRedirect(self):

        response = self.remote.performRequest(method = "HEAD", body = "")
        if response.status == responsecode.MOVED_PERMANENTLY:
            log.info("clone received redirect: " + `self`)
            try:
                redirectURL = uriparse.uriparse(response.getheader("location"))
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
        return self.scheme + "://" + self.host + ":" + `self.port` + self.path
    
    def __hash__(self):
        return `self`.__hash__()
    

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
        
    def announce(self, localResource):
        """
        Inform the remote clone that we have a local clone here.
        """
        from angel_app.resource.remote import clone
        requestBody = clone.makeCloneBody(localResource)
        if not self.ping(): return False
        if not self.exists(): return False
        self.remote.performRequest(method = "PROPPATCH", body = requestBody)
        return True


def makeCloneBody(localResource):
    """
    Make a PROPPATCH body from the local clone for registration with a remote node.
    """
    nodename = AngelConfig.get("maintainer","nodename")
    cc = Clone(nodename, providerport, localResource.relativeURL())
    cloneElement = elements.Clone(rfc2518.HRef(`cc`))
    clonesElement = elements.Clones(*[cloneElement])
    setElement = rfc2518.Set(rfc2518.PropertyContainer(clonesElement))
    propertyUpdateElement = rfc2518.PropertyUpdate(setElement)
    return propertyUpdateElement.toxml()
    

def parseURI(uri):
    (scheme, authority, path, query, fragment) = uriparse.urisplit(uri)
    
    if authority is None: 
        # urisplit may return Nones on failure
        raise ValueError, "Supplied URI is invalid: " + uri
    
    (user, passwd, host, port) = uriparse.split_authority(authority)
    
    return (host, port, path)

def cloneFromURI(uri):
    (host, port, path) = parseURI(uri)
    
    if port is None:  # allow sluggish input leaving off the port number
        port = providerport
    if path == "": # allow sluggish config leaving off the path
        path = "/"
    
    return Clone(host, int(port), path)

    
def cloneFromElement(cc):
    """
    Takes a child element of the Clones element and returns a Clone instance.
    """
    href = str(cc.childOfType(rfc2518.HRef).children[0])
    return cloneFromURI(href)

def clonesFromElement(cloneElement):
    """
    @param cloneElement a Clones element 
    @return a list of corresponding Clone instances
    """
    return [cloneFromElement(cc) for cc in cloneElement.children]

def cloneToElement(cc):
    """
    This is still quite evil, but less so than splitParse etc.
    """
    url = `cc`
    urlElem = rfc2518.HRef(url)
    return elements.Clone(urlElem)

def clonesToElement(cloneList):
    """
    Takes a list of clones and generates a Clones element from it.
    """
    return elements.Clones(*[
                    cloneToElement(cc) for cc in cloneList
                    ])
    