"""
Provide a Mapping from XML-elements to xattr keys.
Handle initialization of attributes with default values.
"""

from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse

from angel_app import elements
from angel_app.resource.local import util

from angel_app.log import getLogger
log = getLogger(__name__)

def resourceID(resource):
    """
    Provide a default resource ID for the metadata initialization.
    """
    if resource.isRepositoryRoot():
        return util.makeResourceID(resource.relativePath())
            
    else:
        return util.getResourceIDFromParentLinks(resource)

def getOnePublicKey(resource):
    """
    This is used in the initialization phase of a resource's meta-data:
    get hold of a meaningful public key.
    """
    if resource.isRepositoryRoot():
        from angel_app.config.internal import loadKeysFromFile    
        return loadKeysFromFile().keys()[0]
    else:
        return resource.parent().publicKeyString()

# a map from xml-elements corresponding to metadata fields to functions taking a resource 
# and returning appropriate values for those metadata fields
defaultMetaData = {
                   elements.Revision           : lambda x: "0",
                   elements.Encrypted          : lambda x: "0",
                   elements.PublicKeyString    : lambda x: getOnePublicKey(x),
                   elements.ContentSignature   : lambda x: "",
                   elements.MetaDataSignature  : lambda x: "",
                   elements.ResourceID         : lambda x: resourceID(x),
                   elements.Clones             : lambda x: None,
                   elements.Children           : lambda x: None
                   }

class PropertyManagerMixin:
    
    def __init__(self):

        # create a per-instance copy of the default generators
        self.defaultValues = dict(defaultMetaData.items())

    def get(self, element):
        
        try:
            self.assertExistence()
        except:
            log.info("failed to look up element %s for resource %s" % (`element`, self.fp.path))
            raise
        
        # the property is available in the property store
        if self.deadProperties().contains(element.qname()):
            return self.deadProperties().get(element.qname())
        
        # the property is not available in the property store,
        # but we have an initializer   
        if element in self.defaultValues.keys():
            df = self.defaultValues[element](self)
            log.debug("Setting property %s to default value %s." % (`element`, `df`))
            if None == df:
                me = element()
            else:
                me = element(df)
                
            self.set(me)
            
            return self.deadProperties().get(element.qname())
        
        else:
            raise KeyError("Attribute for element %s not found on resource %s." % (`element`, self.fp.path))
    
    def assertExistence(self):
        """
        Raise and log an appropriate error if the resource does not exist on the file system.
        """
        import os.path
        if not os.path.exists(self.fp.path):
            error = "Resource %s not found in xattr lookup." % self.fp.path
            log.warn(error)
            raise HTTPError(StatusResponse(responsecode.NOT_FOUND, error))
    
    def getAsString(self, element):
        return "".join([
                        str(child) for child in 
                       self.get(element).children
                                                 ])
        
            
    def getXml(self, element):
        """
        @return the metadata element corresponding to davXMLTextElement
        """
        return  self.get(element).toxml()
        
    def set(self, element):
        
        self.assertExistence()
        
        self.deadProperties().set(element)
            
            