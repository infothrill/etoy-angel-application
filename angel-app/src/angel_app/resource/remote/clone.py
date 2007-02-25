from twisted.web2 import responsecode
from twisted.web2.dav.element import rfc2518
from twisted.web2.dav import davxml
from angel_app import elements
from angel_app.resource.remote import util
from angel_app.resource import IResource
from zope.interface import implements
from angel_app.contrib.ezPyCrypto import key
from angel_app.log import getLogger

log = getLogger("clone")
DEBUG = True

from httplib import HTTPConnection

from angel_app.config import config
AngelConfig = config.getConfig()
providerport = AngelConfig.getint("provider","listenPort")

class Clone(object):
    """
    Provides methods for transparent access to frequently used clone meta data.
    
    TODO: might want to implement property caching
    """
    implements(IResource.IAngelResource)
    
    def __init__(self, host = "localhost", port = providerport, path = "/"):
        """
        @rtype Clone
        @return a new clone
        """
        self.host = host
        self.port = port
        self.path = path
        
        self.propertyCache = {}
        
    def updateCache(self):
        response = self.propertiesDocument(elements.signedKeys)
        properties = response.root_element.childOfType(
                                       rfc2518.Response
                                       ).childOfType(
                                         rfc2518.PropertyStatus
                                         ).childOfType(
                                           rfc2518.PropertyContainer).children
        for property in properties:
            self.propertyCache[property.qname()] = property                            
        
    
    def checkForRedirect(self):

        response = self.__performRequest(method = "HEAD", body = "")
        if response.status == responsecode.MOVED_PERMANENTLY:
            self.path = response.getheader("location")
            log.info("clone received redirect: " + `self`)
    
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

    def __performRequest(self, method = "GET", headers = {}, body = ""):
        DEBUG and log.debug("attempting " + method + " connection to: " + self.host + ":" + `self.port` + " " + self.path)   
        conn = HTTPConnection(self.host, self.port)        
        conn.request(
                 method, 
                 self.path,
                 headers = headers,
                 body = body
                 )
        
        return conn.getresponse()

  
    def stream(self):
        response = self.__performRequest()
        if response.status != responsecode.OK:
            raise "must receive an OK response for GET, otherwise something's wrong"
        return response
    
    
    def propFindAsXml(self, properties):
        """
        @rtype string
        @return the raw XML body of the multistatus response corresponding to the respective PROPFIND request.
        """  
        #DEBUG and log.debug("running PROPFIND on clone " + `self` + " for properties " + `properties` + " with body " + self.__makePropfindRequestBody(properties))
        resp = self.__performRequest(
                              method = "PROPFIND", 
                              headers = {"Depth" : 0}, 
                              body = makePropfindRequestBody(properties)
                              )

        if resp.status != responsecode.MULTI_STATUS:
            DEBUG and log.debug("bad response: " + `resp.status`)
            raise "must receive a MULTI_STATUS response for PROPFIND, otherwise something's wrong, got: " + `resp.status` +\
                resp.read()
        
        data = resp.read()
        #DEBUG and log.debug("PROPFIND body: " + data)
        return data
    
    def propertiesDocument(self, properties):
        """
        @rtype WebDAVDocument
        @return the properties as a davxml document tree.
        """
        return davxml.WebDAVDocument.fromString(
                                               self.propFindAsXml(
                                                                  properties))


    def propertyFindBodyXml(self, property):
        """
        @param property an WebDAVElement corresponding to the property we want to get
        @return the XML of a property find body as appropriate for the supplied property
        @rtype string
        """
        return self.propertiesDocument([property]
                         ).root_element.children[0].children[1].children[0].children[0].toxml()


    
    def uncachedPropertyFindBody(self, property):
        """
        @rtype string
        @return the body of a property consisting of just PCDATA.
        """
        
        DEBUG and log.debug("returned for property "  + `property.qname()` + ": " + self.propertiesDocument([property]).toxml())
        # points to the first dav "prop"-element
        properties = self.propertiesDocument([property]
                                             ).root_element.children[0].children[1].children[0]
        
        return "".join([str(ee) for ee in properties.children[0].children])
    
    def propertyFindBody(self, property):
        """
        @rtype string
        @return the body of a property consisting of just PCDATA.
        
        TODO: this caching scheme could be much improved.
        """
        
        if property.qname() in self.propertyCache.keys():
            properties = self.propertyCache[property.qname()]   
            return "".join([str(ee) for ee in properties.children])
        else:
            return self.uncachedPropertyFindBody(property)
    

    def exists(self): 
        """
        Existence does not imply validity.
        """
        try:
            response = self.__performRequest(method = "HEAD", body = "")
            return response.status == responsecode.OK
        except:
            return False       

    
    def ping(self):
        """
        If an HTTP request can be performed, the remote host is up.
        """
        try:
            response = self.__performRequest(method = "HEAD", body = "")
            return True
        except:
            return False  

    def isCollection(self):
         DEBUG and log.debug("isCollection(): " + self.propertyFindBody(rfc2518.ResourceType) + " " + rfc2518.Collection.sname())
         return self.propertyFindBody(rfc2518.ResourceType) == rfc2518.Collection.sname()
    
    
    def resourceID(self):
        return self.propertyFindBody(elements.ResourceID)
    
    
    def revision(self):
        """
        @rtype int
        @return the clone's revision number.
        """
        try:
            return int(self.propertyFindBody(elements.Revision))
        except:
            log.warn("no revision found on clone: " + `self`)
            return -1
    
    def publicKeyString(self):
        """
        @rtype string
        @return the public key string of the clone.
        """
        return self.propertyFindBody(elements.PublicKeyString)
    
    def validate(self):
        """
        @rtype boolean
        @return if the meta data of a given clone is internally consistent.
        """
        
        
        # TODO: this probably sucks rocks performance-wise, since for each
        # element, we generate a HTTP request...
        toBeVerified = "".join([
                                self.propertyFindBodyXml(element)
                                for element in elements.signedKeys
                                ])
        
        #DEBUG and log.debug("Clone: " + toBeVerified)
        
        pubKey = key()
        try:
            pubKey.importKey(
                         self.propertyFindBody(
                                           elements.PublicKeyString))
            return pubKey.verifyString(
                                   toBeVerified, 
                                   self.propertyFindBody(
                                                     elements.MetaDataSignature))
        except Exception, e:
            log.error(`self` + ": validation failed. Exception: " + `e`)
            return False
        
        
        
    def cloneList(self):
        """
        @rtype [(string, int)]
        @return a list of (string hostname, int port) tuples of clones registered with this clone.
        """

        try:
            prop = self.propertiesDocument(
                                       [elements.Clones]
                                       ).root_element.children[0].children[1].children[0]
                                       
            DEBUG and log.debug(`prop`)
            return clonesFromElement(prop)
            #return [splitParse(
            #               str(clone.children[0].children[0].children[0]))
            #    for clone in prop.children if len(prop.children[0].children) > 0]
        except:
            return []

    def putFile(self, stream):
        """
        Push the file contents, after pushing the relevant properties of a local parent clone to the 
        remote parent clone via a PROPPATCH request.
        
        @see performPushRequest
        """
        resp = self.__performRequest(method = "PUT", body = stream.read())

    def mkCol(self):
        """
        Make a remote collection, after pushing the relevant properties of a local parent clone to the 
        remote parent clone via a PROPPATCH request.
        """
        resp = self.__performRequest(method = "MKCOL", body = "")
        DEBUG and log.msg("response on MKCOL: " + `resp.status`)


    def performPushRequest(self, localClone):
        """
        Push the relevant properties of a local clone to the remote clone via a PROPPATCH request.
        """
        pb = makePushBody(localClone)
        DEBUG and log.debug("pushing metadata:" + pb)
        resp = self.__performRequest(
                                     method = "PROPPATCH", 
                                     body = pb
                                     )
        
        # we probably ignore the returned data, but who knows
        data = resp.read()
        print data
        if resp.status != responsecode.MULTI_STATUS:
            raise "must receive a MULTI_STATUS response for PROPPATCH (received " + \
                `resp.status` + "), otherwise something's wrong"


   
def makePropfindRequestBody(properties):
    """
    @rtype string
    @return XML body of PROPFIND request.
    """
    return rfc2518.PropertyFind(
                rfc2518.PropertyContainer(
                      *[property() for property in properties]
                      )).toxml()
           
def makePushBody(localClone):
    """
    Generate the DAVDocument representation of the required properties of the local clone.
    """
    
    def makeSetElement(elements):
        return rfc2518.Set(
                         rfc2518.PropertyContainer(element))
    
    
    for el in elements.requiredKeys:
        DEBUG and log.debug("makePushBody: " + localClone.deadProperties().get(el.qname()).toxml())
        
    cc = Clone("localhost", providerport, "/" + localClone.relativePath())
    pList = [makeSetElement(element) for element in
             [localClone.deadProperties().get(el.qname()) for el in elements.requiredKeys]
              + [clonesToElement([cc])]]
    
    DEBUG and log.debug(`pList`)
    
    pu = davxml.PropertyUpdate(*pList)
    return pu.toxml()

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
    log.info(cloneUri)
    host, rest = cloneUri.split(":")
    fragments = rest.split("/")
    port = int(fragments[0])
    
    if len(fragments) > 1:
        return host, port, "/" + "/".join(fragments[1:])
    
    return (host, port)

def cloneFromGunk(gunk):
    assert len(gunk) > 1
    assert len(gunk) < 4
    if len(gunk) == 2: return Clone(gunk[0], gunk[1])
    else: return Clone(gunk[0], gunk[1], gunk[2])
    
    
def cloneFromElement(cc):
    """
    Takes an child element of the Clones element and returns a Clone instance.
    """
    return cloneFromGunk(splitParse(str(cc.children[0].children[0])))


def clonesFromElement(cloneElement):
    """
    Takes a Clone element and returns a list of corresponding Clone instances
    """
    return [cloneFromElement(cc) for cc in cloneElement.children]

def clonesToElement(cloneList):
    """
    Takes a list of clones and generates a Clones element from it.
    """
    return elements.Clones(*[
                    elements.Clone(rfc2518.HRef(`cc`)) for cc in cloneList
                    ])
    