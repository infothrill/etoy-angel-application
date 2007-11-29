from twisted.web2 import responsecode
from twisted.web2.dav import davxml
from twisted.web2.dav.element import rfc2518
from zope.interface import implements

from angel_app import elements
from angel_app.resource.IReadonlyPropertyManager import IReadonlyPropertyManager
from angel_app.resource.remote.exceptions import CloneNotFoundError
from angel_app.resource.remote.exceptions import CloneError

class PropertyManager(object):
    """
    Provide a Mapping from XML-elements to (the results of) PROPFIND requests.    
    """
    implements(IReadonlyPropertyManager)
   
    cachedProperties = elements.signedKeys + [elements.MetaDataSignature, rfc2518.ResourceType, elements.Clones]  
  
    def __init__(self, remote):
        self.propertyCache = {}
        self.remote = remote
    
    def getByElement(self, property):
        return self.getProperty(property)
        
    def getProperty(self, property):
        """
        Quite like getProperties, but for a single property only. In contrast to
        getProperties, it doesn't return a davxml.PropertyContainer, but an element
        of the same type as the argument element.
        
        @return the property with a value
        """
        return self.getProperties([property]).childOfType(property)
    
        
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


    def isCollection(self):
        """
        @see IReadOnlyContentManager
        """
        resourceType = self.getProperty(rfc2518.ResourceType)
        if 0 == len(resourceType.children):
            return False
        else:
            return resourceType.children[0].sname() == rfc2518.Collection.sname()
    
    
    def _propertiesDocument(self, properties):
        """
        Perform a PROPFIND request on the clone, returning the response body as an xml document.
        DO NOT use this directly. Use getProperties instead.
        
        @rtype string
        @return the raw XML body of the multistatus response corresponding to the respective PROPFIND request.
        """  
        resp = self.remote.performRequest(
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

        
    def __updateCache(self):
        """
        A single PROPFIND request can request multiple properties. Use this method to update the cache
        of all properties we will likely need.
        """
        properties = okProperties(self._propertiesDocument(self.cachedProperties))
        for property in properties:
            self.propertyCache[property.qname()] = property   

   
def makePropfindRequestBody(properties):
    """
    @rtype string
    @return XML body of PROPFIND request.
    """
    return rfc2518.PropertyFind(
                rfc2518.PropertyContainer(
                      *[property() for property in properties]
                      )).toxml()
                
                

def okProperties(response):
    """
    In addition to the validation carried out by propertiesFromPropfindResponse,    
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
