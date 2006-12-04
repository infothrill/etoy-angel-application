from twisted.web2 import responsecode
from twisted.web2.dav.element import rfc2518
from twisted.web2.dav import davxml
from twisted.python import log
from angel_app import elements
from angel_app.maintainer import util
from ezPyCrypto import key

DEBUG = True

from httplib import HTTPConnection

def splitParse(urlString):
    """
    @rtype (string, int)
    @return (hostname, port)
    """
    words = urlString.split(":")
    return (words[0], int(words[1]))

class Clone(object):
    """
    Provides methods for transparent access to frequently used clone meta data.
    """
    
    def __init__(self, host = "localhost", port = 9999, path = "/"):
        """
        @rtype Clone
        @return a new clone
        """
        self.host = host
        self.port = port
        self.path = path
    
    def __makePropfindRequestBody(self, *properties):
        """
        @rtype string
        @return XML body of PROPFIND request.
        """
        return rfc2518.PropertyFind(
                    rfc2518.PropertyContainer(
                          *[property() for property in properties]
                          )).toxml()
    
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
        DEBUG and log.err("attempting connection to: " + `self.host` + ":" + `self.port` + " " + self.path)   
        conn = HTTPConnection(self.host, self.port)
        conn.request(
                 "GET", 
                 self.path,
                 )
        resp = conn.getresponse()
        if resp.status != responsecode.OK:
            raise "must receive an OK response for GET, otherwise something's wrong"
        return resp
    
    
    def propFindAsXml(self, properties):
        """
        @rtype string
        @return the raw XML body of the multistatus response corresponding to the respective PROPFIND request.
        """  
        conn = HTTPConnection(self.host, self.port)
        DEBUG and log.err("attempting connection to: " + `self.host` + ":" + `self.port` + " " + self.path)   
        conn.request(
                 "PROPFIND", 
                 self.path, 
                 headers = {"Depth" : 0}, 
                 body = self.__makePropfindRequestBody(properties)
                 )
       
        resp = conn.getresponse()
        if resp.status != responsecode.MULTI_STATUS:
            raise "must receive a MULTI_STATUS response for PROPFIND, otherwise something's wrong"
        
        data = resp.read()
        util.validateMulistatusResponseBody(data)
        conn.close()
        #DEBUG and log.err(data)
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
        return self.propertiesDocument(property
                         ).root_element.children[0].children[1].children[0].children[0].toxml()
    
    def propertyFindBody(self, property):
        """
        @rtype string
        @return the body of a property consisting of just PCDATA.
        """
        
        # points to the first dav "prop"-element
        properties = self.propertiesDocument(property
                                             ).root_element.children[0].children[1].children[0]
        
        return "".join([str(ee) for ee in properties.children[0].children])

    
    def ping(self):
        """
        @return whether a clone is reachable
        """
        try:
            # ... well, nearly
            self.revision()
            return True
        except:
            return False
    
    def revision(self):
        """
        @rtype int
        @return the clone's revision number.
        """
        try:
            return int(self.propertyFindBody(elements.Revision))
        except:
            log.err("no revision found on clone: " + `self`)
            return -1
    
    def publicKeyString(self):
        """
        @rtype string
        @return the public key string of the clone.
        """
        try:
            return self.propertyFindBody(elements.PublicKeyString)
        except:
            return ""
    
    def validate(self):
        """
        @rtype boolean
        @return if the meta data of a given clone is internally consistent.
        """
        toBeVerified = "".join([
                                self.propertyFindBodyXml(element)
                                for element in elements.signedKeys
                                ])
        
        DEBUG and log.err("Clone: " + toBeVerified)
        
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
            log.err(`self` + ": validation failed. Exception: " + `e`)
            return False
        
        
        
    def cloneList(self):
        """
        @rtype [(string, int)]
        @return a list of (string hostname, int port) tuples of clones registered with this clone.
        """

        try:
            prop = self.propertiesDocument(
                                       elements.Clones
                                       ).root_element.children[0].children[1].children[0]
                                       
            DEBUG and log.err(`prop`)
            return [splitParse(
                           str(clone.children[0].children[0].children[0]))
                for clone in prop.children if len(prop.children[0].children) > 0]
        except:
            return []

    def putFile(self, stream):
        """
        Push the relevant properties of a local clone to the remote clone via a PROPPATCH request.
        """
        conn = HTTPConnection(self.host, self.port)       
        conn.request(
                 "PUT", 
                 self.path,
                 stream.read()
                 )


    def performPushRequest(self, localClone):
        """
        Push the relevant properties of a local clone to the remote clone via a PROPPATCH request.
        """
        conn = HTTPConnection(self.host, self.port)
        DEBUG and log.err("attempting connection to: " + `self`)    
        conn.request(
                 "PROPPATCH", 
                 self.path,
                 body = makePushBody(localClone)
                 )
       
        resp = conn.getresponse()
        
        # we probably ignore the returned data, but who knows
        data = resp.read()
        print data
        if resp.status != responsecode.MULTI_STATUS:
            raise "must receive a MULTI_STATUS response for PROPPATCH (received " + \
                `resp.status` + "), otherwise something's wrong"
        conn.close()
           
def makePushBody(localClone):
    """
    Generate the DAVDocument representation of the required properties of the local clone.
    """
    
    for el in elements.requiredKeys:
        log.err("makePushBody: " + `el.qname()`)
    pList = [
             rfc2518.Set(
                         rfc2518.PropertyContainer(
                                      localClone.deadProperties().get(el.qname())))
             for el in elements.requiredKeys
             ]
    
    DEBUG and log.err(`pList`)
    
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


def iterateClones(cloneSeedList, publicKeyString):
    """
    get all the clones of the (valid) clones we have already looked at
    which are not among any (including the invalid) of the clones we
    have already looked at, and validate those clones.
    
    @rtype ([Clone], [Clone])
    @return a tuple of ([the list of valid clones], [the list of checked clones])
    """  
    import copy
    toVisit = copy.copy(cloneSeedList)
    allVisitedClones = []
    visited = {}
    good = []
    bad = []
    ugly = []
    revision = 0
    
    while len(toVisit) != 0:
        # there are clones that we need to inspect
        
        # pop the next clone from the queue
        cc = toVisit[0]
        log.err("inspecting clone: " + `cc`)
        toVisit = toVisit[1:]
        
        if visited.has_key(cc):
            # we have already looked at this clone -- don't bother with it
            DEBUG and log.err("iterateClones: " + `cc` + " ignoring")
            continue
               
        # otherwise, mark the clone as checked and proceed
        allVisitedClones.append(cc)
        visited[cc] = cc
        
        if not cc.ping():
            # this clone is unreachable, ignore it
            continue
        
        if cc.publicKeyString() != publicKeyString:
            # an invalid clone
            DEBUG and log.err("iterateClones: " + `cc` + " wrong public key")
            bad.append(cc)
            continue
        
        if not cc.validate():
            # an invalid clone
            DEBUG and log.err("iterateClones: " + `cc` + " invalid signature")
            bad.append(cc)
            continue
        
        rr = cc.revision()
        
        if rr < revision:
            # too old
            DEBUG and log.err("iterateClones: " + `cc` + "too old: " + `rr` + " < " + `revision`)
            bad.append(cc)
            continue
        
        if rr > revision:
            # hah! the clone is newer than anything
            # we've seen so far. all the clones we thought
            # were good are in fact bad.
            DEBUG and log.err("iterateClones: " + `cc` + "very new: " + `rr` + " > " + `revision`)
            bad.extend(good)
            good = []
            revision = rr
        
        # we only arrive here if the clone is valid and sufficiently new
        good.append(cc)
        DEBUG and log.err("iterateClones: adding good clone: " + `cc`)
        toVisit += [Clone(host, port) for host, port in cc.cloneList()]
        
        

    DEBUG and log.err("iterateClones: good clones: " + `good`)
    DEBUG and log.err("iterateClones: bad clones: " + `bad`)
    
    return good, bad