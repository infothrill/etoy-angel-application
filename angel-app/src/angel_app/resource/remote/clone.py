import socket

from twisted.web2 import responsecode
from twisted.web2.dav.element import rfc2518
from zope.interface import implements

from angel_app import elements
from angel_app import uri
from angel_app.config import config
from angel_app.log import getLogger
from angel_app.resource import IResource
from angel_app.resource.remote.contentManager import ContentManager
from angel_app.resource.remote.httpRemote import HTTPRemote
from angel_app.resource.remote.propertyManager import PropertyManager
from angel_app.resource.resource import Resource

from angel_app.resource.remote.exceptions import CloneError
from angel_app.resource.remote.exceptions import CloneNotFoundError

log = getLogger(__name__)


AngelConfig = config.getConfig()
providerport = AngelConfig.getint("provider","listenPort")

def typed(expr, ref):
    if not type(expr) == type(ref):
        raise TypeError, "Expected type " + `type(ref)` + " but found: " + `type(expr)` 

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
        typed(scheme, '')
        self.scheme = scheme
        
        # the host name or ip
        typed(host, '')
        self.host = host
        
        # a port number
        typed(port, 0)
        self.port = port
        
        # a path string. must be valid as part of an absolute URL (i.e. quoted, using "/")
        typed(path, '')
        self.path = path
        
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
        """
        if the clone is valid, we must be able to reconstruct the host, port, path from the string representation.
        TODO: this is currently broken.
        """
        rc = cloneFromURI(self.toURI())
        
        if not rc == self:
            log.info("Clone doesn't self-match: %s vs. %s" % (`self`, `rc`))
            raise CloneError("Invalid host for clone: %s %s" % (`self`, `rc`))                                             
        
    
    def checkForRedirect(self):
        """
        Check for redirect on this clone.
        
        @return this clone, if no redirect happened, otherwise return a new clone c
        orresponding to the redirect target
        """

        response = self.remote.performRequest(method = "HEAD", body = "")
        if response.status == responsecode.MOVED_PERMANENTLY:
            log.info("Received redirect for clone: " + `self`)
            redirectlocation = response.getheader("location")
            # TODO: how to verify/validate redirectlocation ?
            # RFCs state it should be URI, but we gat a path only
            redirectClone = Clone(self.host, self.port, redirectlocation)
            log.info("Redirecting to: %s" % `redirectClone`)
            return redirectClone
        else:
            return self
    
    def __eq__(self, clone):
        """
        @rtype boolean
        Comparison operator.
        """
        return self.host == clone.host and self.port == clone.port
    
    def __repr__(self):
        return self.toURI()
    
    def __hash__(self):
        return `self`.__hash__()

    def toURI(self):
        return self.scheme + "://" + formatHost(self.host) + ":" + `self.port` + self.path
            

    def exists(self): 
        """
        Keep in mind that existence does not imply validity.
        """
                
        self.validatePath()
        self.validateHostPort()
        
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

def formatHost(hostname = "localhost"):
    if not isNumericIPv6Address(hostname):
        return hostname
    else:
        return "[" + hostname + "]"

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


def cloneFromURI(_uri, defaultHost = None):
    """
    Return a new instance of a clone given the URI
    """
    pp = uri.parse(_uri)
    log.debug("parsed URI: %s" % `pp`)
    # check optional argument defaultHost
    if defaultHost is None:
        _host = str(pp.host)
    else:
        _host = defaultHost
    # if port is empty, fallback to default 
    if pp.port == "":
        from angel_app.config.defaults import providerPublicListenPort
        port = providerPublicListenPort
    else:
        port = pp.port
    # if path is empty, fallback to root "/"
    _path = "".join(pp.path)
    if _path == '':
        _path = '/'
    return Clone(_host, int(port), _path)

def tryNumericAddress(family = socket.AF_INET, address = "127.0.0.1"):
    """
    @return whether (numerice) address is a valid member of family
    """
    try:
        socket.inet_pton(family, address)
        return True
    except socket.error:
        return False
    
def isNumericIPv6Address(address):
    return tryNumericAddress(socket.AF_INET6, address)

    
def cloneFromElement(cc):
    """
    Takes a child element of the Clones element and returns a Clone instance.
    """
    href = str(cc.childOfType(rfc2518.HRef).children[0])
    return cloneFromURI(href)

def maybeCloneFromElement(cc):
    """
    @see cloneFromElement
    
    The difference is that if any exceptions are raised, None is returned.
    """
    try:
        return cloneFromElement(cc)
    except:
        log.info("ignoring invalid clone uri: " + `cc`)
        return None

def clonesFromElement(cloneElement):
    """
    @param cloneElement a Clones element 
    @return a list of corresponding Clone instances (ignoring those for which a parse failed)
    """
    mc = (maybeCloneFromElement(cc) for cc in cloneElement.children)
    return [cc for cc in mc if cc != None]

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
    