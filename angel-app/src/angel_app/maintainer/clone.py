from twisted.web2 import responsecode
from twisted.web2.dav.element.rfc2518 import PropertyFind, PropertyContainer
from twisted.web2.dav import davxml

from angel_app import elements
from ezPyCrypto import key

DEBUG = True

from httplib import HTTPConnection

class Clone(object):
    """
    Provides methods for transparent access to frequently used clone meta data.
    """
    
    def __init__(self, host = "localhost", port = 9999):
        self.host = host
        self.port = port
    
    def __makeRequestBody(self, *properties):
        """
        Generate XML body of PROPFIND request.
        """
        return PropertyFind(
                    PropertyContainer(
                          *[property() for property in properties]
                          )).toxml()
    
    def __eq__(self, clone):
        """
        Comparison operator.
        """
        return self.host == clone.host and self.port == clone.port
    
    def propertiesAsXml(self, properties):
        """
        Returns the raw XML body of the multistatus response
        corresponding to the respective PROPFIND request.
        """  
        conn = HTTPConnection(self.host, self.port)       
        conn.request(
                 "PROPFIND", 
                 "/", 
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
        Return the properties as a davxml document tree.
        """
        return davxml.WebDAVDocument.fromString(
                                               self.propertiesAsXml(
                                                                  properties))
    
    def propertyBody(self, property):
        """
        Return the body of an property consisting of just PCDATA.
        """
        
        # points to the first dav "prop"-element
        properties = self.propertiesDocument(property
                                             ).root_element.children[0].children[1].children[0]
        
        return "".join([str(ee) for ee in properties.children[0].children])

    
    def revision(self):
        """
        The clone's revision number.
        """
        return int(self.propertyBody(elements.Revision))
    
    def validate(self):
        """
        Assert that the meta data of a given clone is internally consistent.
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
        Returns a list of (string hostname, int port) tuples of clones registered
        with this clone.
        """
        prop = self.propertiesDocument(elements.Clones).root_element.children[0].children[1].children[0]
        
        def splitAndParse(localHostPortString):
            words = localHostPortString.split(":")
            return (words[0], int(words[1]))
        
        return [
                splitAndParse(
                              str(clone.children[0].children[0].children[0]))
                for clone in prop.children
                ]
         
    