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
from netaddress.rfc3986 import path_absolute
from pyparsing import ParseException
log = getLogger(__name__)

PROVIDER_PUBLIC_LISTEN_PORT = 6221

AngelConfig = config.getConfig()
providerport = AngelConfig.getint("provider","listenPort")

def typed(expr, ref):
    if not type(expr) == type(ref):
        raise TypeError, "Expected type " + repr(type(ref)) + " but found: " + repr(type(expr))

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

        # does this URI correspond to the result of a redirect (MOVED_PERMANENTLY)?
        self.redirected = False
        
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
            raise CloneError("Invalid path for clone: " + self.path)

        if not len(self.path) > 0:
            raise CloneError("Need non-empty path for clone. Got: " + self.path)
        
        if not self.path[0] == "/":
            raise CloneError("Need absolute path for clone. Got: " + self.path)
        
    def validateHostPort(self):
        """
        if the clone is valid, we must be able to reconstruct the host, port, path from the string representation.
        TODO: this is currently just a quick fix. It would be better to compare the clones directly, but for some
        reason, this is broken.
        """
        rc = cloneFromURI(self.toURI())
        
        if not rc == self:
            log.info("Clone doesn't self-match: %s vs. %s" % (repr(self), repr(rc)))
            raise CloneError("Invalid host for clone: %s %s" % (repr(self), repr(rc)))                                             
        
    
    def checkForRedirect(self):
        """
        Check for redirect on this clone.
        
        @return this clone, if no redirect happened, otherwise return a new clone
        corresponding to the redirect target
        """

        response = self.remote.performRequest(method = "HEAD", body = "")
        if response.status == responsecode.MOVED_PERMANENTLY:
            log.info("Received redirect for clone: " + str(self))
            
            if self.redirected:
                errMsg = "Guarding against multiple redirects for " + str(self)
                raise CloneError(errMsg)
            
            redirectlocation = response.getheader("location")
            # TODO: how to verify/validate redirectlocation ?
            # RFCs state it should be URI, but we get a path only
            # for the time being, we require it's an absolute path
            try:
                path_absolute.parseString(redirectlocation)
            except ParseException:
                errorMessage = "Invalid redirect. Must be an absolute path. Found: " + redirectlocation
                raise CloneError(errorMessage)
            redirectClone = Clone(self.host, self.port, redirectlocation)
            redirectClone.redirected = True
            log.info("Redirecting to: %s" % str(redirectClone))
            return redirectClone
        else:
            return self
    
    def __eq__(self, clone):
        """
        @rtype boolean
        Comparison operator.
        Two clones are equal exactly if they point to the same resource (they have the same URI representation).
        """
        if type(self) != type(clone):
            return False
        
        #log.debug("clones %s %s are equal: %s" % (self.toURI(), clone.toURI(), `self.toURI() == clone.toURI()`))
        return self.toURI() == clone.toURI()
    
    def __repr__(self):
        return self.toURI()
        # pk: this reallt 'should' look more like the stuff below, but for now, we rely on URIs 
        #return "Clone('%s', '%s', '%s', '%s')" % (self.host, self.port, self.path, self.scheme)

    def __str__(self):
        return self.toURI()

    def __hash__(self):
        return str(self).__hash__()

    def toURI(self):
        return self.scheme + "://" + formatHost(self.host) + ":" + str(self.port) + self.path
    
    def getHost(self):
        return self.host

    def exists(self): 
        """
        Keep in mind that existence does not imply validity.
        """
        log.debug("exists %s" % repr(self))
                
        self.validatePath()
        self.validateHostPort()
        
        try:
            response = self.remote.performRequest(method = "HEAD")
            return response.status == responsecode.OK
        except KeyboardInterrupt:
            raise
        except:
            return False       

    
    def ping(self):
        """
        @return whether the remote host is reachable
        """
        log.debug("ping %s" % repr(self))
        try:
            dummyresponse = self.remote.performRequestWithTimeOut(method = "HEAD")
            return True
        except KeyboardInterrupt:
            raise
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
        except KeyboardInterrupt:
            raise
        except:
            return []
        
    def announce(self, localResource):
        """
        Inform the remote clone that we have a local clone here. This method
        may fail to announce the remote clone.
        """
        log.debug("announcing local clone to %s" % repr(self))
        requestBody = makeCloneBody(localResource)
        # no point in ping() or exists(): the PROPPATCH will either work or fail ;-)
        try:
            self.remote.performRequest(method = "PROPPATCH", body = requestBody)
        except KeyboardInterrupt:
            raise
        except Exception, e:
            log.warn("Announcement to clone %s failed" % repr(self), exc_info = e)
            return False
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
    cloneElement = elements.Clone(rfc2518.HRef(str(cc)))
    clonesElement = elements.Clones(*[cloneElement])
    setElement = rfc2518.Set(rfc2518.PropertyContainer(clonesElement))
    propertyUpdateElement = rfc2518.PropertyUpdate(setElement)
    return propertyUpdateElement.toxml()


def cloneFromURI(_uri, defaultHost = None):
    """
    Return a new instance of a clone given the URI
    """
    pp = uri.parse(_uri)
    # check optional argument defaultHost
    if defaultHost is None:
        _host = str(pp.host)
    else:
        _host = defaultHost
    # if port is empty, fallback to default 
    if pp.port == "":
        port = PROVIDER_PUBLIC_LISTEN_PORT
    else:
        port = pp.port
    # if path is empty, fallback to root "/"
    _path = "".join(pp.path)
    if _path == '':
        _path = '/'
    return Clone(_host, int(port), _path)

def tryNumericAddress(family = socket.AF_INET, address = "127.0.0.1"):
    """
    Test if address and address family match. 
    
    @param family: one of socket.AF_*
    @param address: string representation of address
    @return: boolean whether (numeric) address is a valid member of family
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
    except KeyboardInterrupt:
        raise
    except:
        log.info("ignoring invalid clone uri: " + str(cc))
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
    url = str(cc)
    urlElem = rfc2518.HRef(url)
    return elements.Clone(urlElem)

def clonesToElement(cloneList):
    """
    Takes a list of clones and generates a Clones element from it.
    """
    return elements.Clones(*[
                    cloneToElement(cc) for cc in cloneList
                    ])
    