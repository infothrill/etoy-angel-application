"""
Provide a Mapping from XML-elements to xattr keys.
Handle initialization of attributes with default values.
"""
from angel_app import elements
from angel_app.log import getLogger
from angel_app.resource.IReadonlyPropertyManager import IReadonlyPropertyManager
from twisted.web2 import responsecode
from twisted.web2.dav.element.base import WebDAVElement
from twisted.web2.dav.xattrprops import xattrPropertyStore
from twisted.web2.http import HTTPError, StatusResponse
from zope.interface import implements
import time


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
                   elements.Revision.qname()           : lambda x: elements.Revision.fromString("0"),
                   elements.Encrypted.qname()          : lambda x: elements.Encrypted.fromString("0"),
                   elements.PublicKeyString.qname()    : lambda x: elements.PublicKeyString.fromString(getOnePublicKey(x.resource)),
                   elements.ContentSignature.qname()   : lambda x: elements.ContentSignature.fromString(""),
                   elements.MetaDataSignature.qname()  : lambda x: elements.MetaDataSignature.fromString(""),
                   elements.ResourceID.qname()         : lambda x: elements.ResourceID.fromString(makeResourceID(x.resource.relativePath())),
                   elements.Clones.qname()             : lambda x: inheritClones(x.resource),
                   elements.Children.qname()           : lambda x: elements.Children()
                   }

class PropertyManager(xattrPropertyStore):
    """
    I am an xattrPropertyStore with default values.
    
    TODO: consider adding default value handling for contains() and listProperties()
    """
    implements(IReadonlyPropertyManager)
    
    def __init__(self, resource):
        super(PropertyManager, self).__init__(resource)
        # create a per-instance copy of the default generators
        self.defaultValues = dict(defaultMetaData.items())

    def isCollection(self):
        """
        This is ass-backwards, but isCollection is provided by DAVFile.
        """
        return resource.isCollection()

    def get(self, qname):
        
        assert type(qname) == type(WebDAVElement.qname())
        
        try:
            self.assertExistence()
        except:
            log.info("failed to look up element %s for resource %s" % (`qname`, self.resource.fp.path))
            raise
        
        # the property is available in the property store
        if super(PropertyManager, self).contains(qname):
            return super(PropertyManager, self).get(qname)
        
        # the property is not available in the property store,
        # but we have an initializer   
        if qname in self.defaultValues.keys():
            df = self.defaultValues[qname](self)
            self.set(df)
            return super(PropertyManager, self).get(qname)
        
        else:
            raise KeyError("Attribute for element %s not found on resource %s." % 
                           (`qname`, self.resource.fp.path))
    
    def assertExistence(self):
        """
        Raise and log an appropriate error if the resource does not exist on the file system.
        """
        import os.path
        if not os.path.exists(self.resource.fp.path):
            error = "Resource %s not found in xattr lookup." % self.fp.path
            log.warn(error)
            raise HTTPError(StatusResponse(responsecode.NOT_FOUND, error))
        
    def set(self, element):
        
        self.assertExistence()
        
        super(PropertyManager, self).set(element)
            
            