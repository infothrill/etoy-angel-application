from twisted.web2 import responsecode
from twisted.web2.dav.element.rfc2518 import PropertyFind, PropertyContainer
from twisted.web2.dav import davxml

from angel_app import elements
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
    
    def __makeRequestBody(self, *properties):
        """
        @rtype string
        @return XML body of PROPFIND request.
        """
        return PropertyFind(
                    PropertyContainer(
                          *[property() for property in properties]
                          )).toxml()
    
    def __eq__(self, clone):
        """
        @rtype boolean
        Comparison operator.
        """
        return self.host == clone.host and self.port == clone.port
    
    def propertiesAsXml(self, properties):
        """
        @rtype string
        @return the raw XML body of the multistatus response corresponding to the respective PROPFIND request.
        """  
        conn = HTTPConnection(self.host, self.port)       
        conn.request(
                 "PROPFIND", 
                 self.path, 
                 headers = {"Depth" : 0}, 
                 body = self.__makeRequestBody(properties)
                 )
       
        resp = conn.getresponse()
        if resp.status != responsecode.MULTI_STATUS:
            raise "must receive a MULTI_STATUS response for PROPFIND, otherwise something's wrong"
        
        data = resp.read()
        conn.close()
        return data
    
    def propertiesDocument(self, properties):
        """
        @rtype WebDAVDocument
        @return the properties as a davxml document tree.
        """
        return davxml.WebDAVDocument.fromString(
                                               self.propertiesAsXml(
                                                                  properties))
    
    def propertyBody(self, property):
        """
        @rtype string
        @return the body of a property consisting of just PCDATA.
        """
        
        # points to the first dav "prop"-element
        properties = self.propertiesDocument(property
                                             ).root_element.children[0].children[1].children[0]
        
        return "".join([str(ee) for ee in properties.children[0].children])

    
    def revision(self):
        """
        @rtype int
        @return the clone's revision number.
        """
        return int(self.propertyBody(elements.Revision))
    
    def publicKeyString(self):
        """
        @rtype string
        @return the public key string of the clone.
        """
        return self.propertyBody(elements.PublicKeyString)
    
    def validate(self):
        """
        @rtype boolean
        @return if the meta data of a given clone is internally consistent.
        """
        toBeVerified = "".join([
                                self.propertyBody(element)
                                for element in
                                [elements.Revision, elements.ContentSignature, elements.PublicKeyString, elements.Deleted]])
        
        pubKey = key()
        pubKey.importKey(
                         self.propertyBody(
                                           elements.PublicKeyString))
        
        return pubKey.verifyString(
                                   toBeVerified, 
                                   self.propertyBody(
                                                     elements.MetaDataSignature))
        
    def cloneList(self):
        """
        @rtype [(string, int)]
        @return a list of (string hostname, int port) tuples of clones registered with this clone.
        """
        prop = self.propertiesDocument(elements.Clones).root_element.children[0].children[1].children[0]
        
        return [splitParse(
                           str(clone.children[0].children[0].children[0]))
                for clone in prop.children]
         
    
    

def getClonesOf(clonesList):
    """
    @type clonesList [Clone]
    @param clonesList list of clones we want to get the clones from
    @rtype [Clone]
    @return list of clones of the clones in clonesList
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

def getValidatedClones(clonesList, publicKeyString, revision):
    """
    @rtype [Clone]
    @return 
    """
    return [clone for clone in clonesList 
            if clone.validate() 
            and clone.revision() >= revision
            and clone.publicKeyString() == publicKeyString]


def getMostCurrentClones(clonesList):
    """
    @rtype [Clone]
    @return the most current clones from the clonesList
    """
    newest = max([clone.revision() for clone in clonesList])    
    return [clone for clone in clonesList if clone.revision() == newest]


def iterateClones(validCloneList, checkedCloneList, publicKeyString):
    """
    get all the clones of the (valid) clones we have already looked at
    which are not among any (including the invalid) of the clones we
    have already looked at, and validate those clones.
    
    @rtype ([Clone], [Clone])
    @return a tuple of ([the list of valid clones], [the list of checked clones])
    """  
    unvalidatedClones, checkedCloneList = getUncheckedClones(
                             getClonesOf(validCloneList),
                             checkedCloneList)
    
    validCloneList = getMostCurrentClones(
                                          getValidatedClones(
                                                             unvalidatedClones, 
                                                             publicKeyString, 
                                                             validCloneList[0].revision()
                                                             ) + validCloneList
                                          )
    if unvalidatedClones == []:
        return validCloneList, checkedCloneList
    else:
        return iterateClones(validCloneList, checkedCloneList, publicKeyString)