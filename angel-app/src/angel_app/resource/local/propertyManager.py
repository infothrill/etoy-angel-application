"""
Provide a Mapping from XML-elements to xattr keys.
Handle initialization of attributes with default values.
"""
import time

from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse

from angel_app import elements
from angel_app.log import getLogger
log = getLogger(__name__)

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

  
def inheritClones(resource):
    """
    Inherit the clones list from the parent resource -- useful for initialization.
    
    Note that this will recursively initialize the clone field all parent resources, 
    until one parent is found that does have clones. Will raise a RuntimeError if the root node has no
    clones.
    """
    if resource.isRepositoryRoot():
        return elements.Clones() # Root resource can not inherit clones, since it has no parent.

    from angel_app.resource.remote import clone
        
    parentClones = resource.parent().clones()
    
    def adaptPaths(parentClone):
        """
        Given a parent's clone, generate a tentative clone for this resource by appending
        the resource's name to the path of the parent's clone.
        
        @param parentClone: a clone instance of the parent.
        @return : a tentative clone instance of this resource.
        """
        newPath = parentClone.path
        if newPath[-1] != "/":
            newPath += "/"
        newPath += resource.quotedResourceName()
        return clone.Clone(
                           parentClone.host, 
                           parentClone.port, 
                           newPath)
        
    inheritedClones = map(adaptPaths, parentClones)
    clonesElement = clone.clonesToElement(inheritedClones)
    return clonesElement



def makeResourceID(relativePath = ""):
    """
    Generate a new resourceID for a (new) resource.
    """
    return relativePath + `time.gmtime()`

# a map from xml-elements corresponding to metadata fields to functions taking a resource 
# and returning appropriate values for those metadata fields
defaultMetaData = {
                   elements.Revision           : lambda x: elements.Revision.fromString("0"),
                   elements.Encrypted          : lambda x: elements.Encrypted.fromString("0"),
                   elements.PublicKeyString    : lambda x: elements.PublicKeyString.fromString(getOnePublicKey(x)),
                   elements.ContentSignature   : lambda x: elements.ContentSignature.fromString(""),
                   elements.MetaDataSignature  : lambda x: elements.MetaDataSignature.fromString(""),
                   elements.ResourceID         : lambda x: elements.ResourceID.fromString(makeResourceID(x.relativePath())),
                   elements.Clones             : lambda x: inheritClones(x),
                   elements.Children           : lambda x: elements.Children()
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
            self.set(df)
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
        
    def set(self, element):
        
        self.assertExistence()
        
        self.deadProperties().set(element)
            
            