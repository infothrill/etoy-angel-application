"""
Provide a Mapping from XML-elements to xattr keys.
Handle initialization of attributes with default values.
"""
import os.path
import time
import urllib

from twisted.web2 import responsecode
from twisted.web2.dav.element.base import WebDAVElement
from twisted.web2.dav.xattrprops import xattrPropertyStore
from twisted.web2.http import HTTPError, StatusResponse
from zope.interface import implements

from angel_app import elements
from angel_app.log import getLogger
from angel_app.resource.IReadonlyPropertyManager import IReadonlyPropertyManager
from angel_app.resource.remote.clone import clonesToElement
from angel_app.resource.IDeadPropertyStore import IDeadPropertyStore


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
        if len(newPath) == 0:
            raise ValueError, "Invalid path: %s for clone %s" % (newPath, `parentClone`)
        
        if newPath[-1] != "/":
            newPath += "/"
        newPath += urllib.quote(resource.resourceName())
        return clone.Clone(
                           parentClone.host, 
                           parentClone.port, 
                           newPath)
        
    inheritedClones = map(adaptPaths, parentClones)
    return inheritedClones

def inheritClonesElement(resource):
    if resource.isRepositoryRoot():
        return elements.Clones() # Root resource can not inherit clones, since it has no parent.
    inheritedClones = inheritClones(resource)
    clonesElement = clonesToElement(inheritedClones)
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
                   elements.Clones.qname()             : lambda x: inheritClonesElement(x.resource),
                   elements.Children.qname()           : lambda x: elements.Children()
                   }

def getDefaultPropertyManager(_resource):
    return PropertyManager(_resource, xattrPropertyStore(_resource))

class PropertyManager(object):
    """
    A wrapper around a deadPropertyStore (e.g. an xattrProps instance) that provides
    default value handling.
    
    To be able to support both xattrPropertyStores and (future) ZODB-based property stores,
    this is from now on implemented via composition rather than inheritance. The store implementation
    to be used at run-time is provided to the constructor (i.e. depdendency injection).
    
    TODO: consider adding default value handling for contains() and listProperties()
    """
    implements(IReadonlyPropertyManager, IDeadPropertyStore)
    
    def __init__(self, _resource, _store):
        self.resource = _resource
         
        self.store = _store
        # create a per-instance copy of the default generators
        # TODO: review: is this necessary?
        self.defaultValues = dict(defaultMetaData.items())

    def isCollection(self):
        """
        This is ass-backwards, but isCollection is provided by DAVFile.
        """
        return self.resource.isCollection()
    
    def contains(self, element):
        return self.store.contains(element)
    
    def list(self):
        return self.store.list()
    
    def delete(self, qname):
        return self.store.delete(qname)

    def getByElement(self, property):
        return self.get(property.qname())

    def get(self, qname):
        
        assert type(qname) == type(WebDAVElement.qname())
        
        # if the resource doesn't yet exist, return a default value
        if not os.path.exists(self.resource.fp.path):
            if qname in self.defaultValues.keys():
                return self.defaultValues[qname](self)
            
        try:
            self.assertExistence()
        except:
            log.info("failed to look up element %s for resource %s" % (`qname`, self.resource.fp.path))
            raise
        
        # the property is available in the property store
        if self.store.contains(qname):
            return self.store.get(qname)
        
        # the property is not available in the property store,
        # but we have an initializer   
        if qname in self.defaultValues.keys():
            df = self.defaultValues[qname](self)
            self.set(df)
            return self.store.get(qname)
        
        else:
            raise KeyError("Attribute for element %s not found on resource %s." % 
                           (`qname`, self.resource.fp.path))
    
    def assertExistence(self):
        """
        Raise and log an appropriate error if the resource does not exist on the file system.
        """
        if not os.path.exists(self.resource.fp.path):
            error = "Resource %s not found in xattr lookup." % self.resource.fp.path
            log.warn(error)
            raise HTTPError(StatusResponse(responsecode.NOT_FOUND, error))
        
    def set(self, element):
        
        self.assertExistence()
        
        self.store.set(element)
            
            