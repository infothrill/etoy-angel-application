"""
Provide a Mapping from XML-elements to xattr keys.
Hanlde initialization of attributes with default values.
"""

import twisted.web2.responsecode
from twisted.web2.http import HTTPError

from angel_app import elements
from angel_app.resource.local import util

from angel_app.log import getLogger
log = getLogger(__name__)

def resourceID(resource):
        if resource.isRepositoryRoot():
            return util.makeResourceID(resource.relativePath())
            
        else:
            return util.getResourceIDFromParentLinks(resource)

def getOnePublicKey():
    from angel_app.config.internal import loadKeysFromFile
    
    return loadKeysFromFile().keys()[0]

# a map from xml-elements corresponding to metadata fields to functions taking a resource 
# and returning appropriate values for those metadata fields
defaultMetaData = {
                   elements.Revision           : lambda x: "0",
                   elements.Encrypted          : lambda x: "0",
                   elements.PublicKeyString    : lambda x: x.parent() and x.parent().publicKeyString() or getOnePublicKey(),
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
        
        self.assertExistence()
        
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
        if not self.fp.exists():
            error = "Resource %s not found in xattr lookup." % self.fp.path
            log.warn(error)
            raise HTTPError(responsecode.NOT_FOUND, error)
    
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
            
            