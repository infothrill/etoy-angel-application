"""
Provide a Mapping from XML-elements to xattr keys.
Handle initialization of attributes with default values.
"""
import os.path
import time
import urllib

from twisted.web2 import responsecode
from twisted.web2.dav.element.base import WebDAVElement
from angel_app.resource.local.DirectoryDeadProperties import DirectoryDeadProperties
from twisted.web2.http import HTTPError, StatusResponse
from zope.interface import implements

from angel_app import elements
from angel_app.log import getLogger
from angel_app.resource.IReadonlyPropertyManager import IReadonlyPropertyManager
from angel_app.resource.remote.clone import clonesToElement
from angel_app.resource.IDeadPropertyStore import IDeadPropertyStore
from angel_app.admin.secretKey import defaultPublicKey


log = getLogger(__name__)

def getOnePublicKey(resource):
    """
    This is used in the initialization phase of a resource's meta-data:
    get hold of a meaningful public key.
    """
    if resource.isRepositoryRoot():
        return defaultPublicKey()
    else:
        return resource.parent().publicKeyString()

  
def inheritClones(resource):
    """
    Inherit the clones list from the parent resource -- useful for initialization.
    
    Note that this will recursively initialize the clone field all parent resources, 
    until one parent is found that does have clones. Will raise a RuntimeError if the root node has no
    clones.
    One exception is being made for the repository root: here we do not fail,
    but silently return an empty list.
    """
    from angel_app.resource.remote import clone
        
    if resource.isRepositoryRoot():
        return []

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

# A map from xml-elements corresponding to metadata fields to functions taking a resource 
# and returning appropriate values for those metadata fields.
# We don't use lambda functions to avoid problems when pickling
def _revision_qname(x): elements.Revision.fromString("0")
def _encrypted_qname(x): elements.Encrypted.fromString("0")
def _pubkeystring_qname(x): elements.PublicKeyString.fromString(getOnePublicKey(x.resource))
def _contentsignature_qname(x): elements.ContentSignature.fromString("")
def _metadatasignature_qname(x): elements.MetaDataSignature.fromString("")
def _resourceid_qname(x): elements.ResourceID.fromString(makeResourceID(x.resource.relativePath()))
def _clones_qname(x): inheritClonesElement(x.resource)
def _children_qname(x): elements.Children()
defaultMetaData = {
                   elements.Revision.qname()           : _revision_qname,
                   elements.Encrypted.qname()          : _encrypted_qname,
                   elements.PublicKeyString.qname()    : _pubkeystring_qname,
                   elements.ContentSignature.qname()   : _contentsignature_qname,
                   elements.MetaDataSignature.qname()  : _metadatasignature_qname,
                   elements.ResourceID.qname()         : _resourceid_qname,
                   elements.Clones.qname()             : _clones_qname,
                   elements.Children.qname()           : _children_qname
                   }

def getDefaultPropertyManager(_resource):
    #return PropertyManager(_resource, xattrPropertyStore(_resource))
    return PropertyManager(_resource,  DirectoryDeadProperties(_resource))

class PropertyManager(object):
    """
    A wrapper around a deadPropertyStore (e.g. an xattrProps instance) that provides
    default value handling.
    
    To be able to support both xattrPropertyStores and (future) ZODB-based property stores,
    this is from now on implemented via composition rather than inheritance. The store implementation
    to be used at run-time is provided to the constructor (i.e. dependency injection).
    
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
        return (self.store.contains(element) or (element in self.defaultValues.keys()))
    
    def list(self):
        union = (set(self.store.list()) | set(self.defaultValues.keys()))
        return [e for e in union]
    
    def delete(self, qname):
        """
        TODO: need to be able to handle default values as well?
        """
        return self.store.delete(qname)

    def getByElement(self, property):
        return self.get(property.qname())

    def get(self, qname):
        
        assert type(qname) == type(WebDAVElement.qname())
        
        # the property is available in the property store
        if self.store.contains(qname):
            return self.store.get(qname)
        
        # the property is not available in the property store,
        # but we have an initializer   
        if qname in self.defaultValues.keys():
            dp = self.defaultValues[qname](self)
            try:
                # try to write the metadata -- this may fail e.g. if 
                # the metadata container does not yet exist on the file system
                # TODO: I don't feel good about this "solution" -- review when time permits
                self.set(dp)
            except Exception, e:
                log.info("Failed to persist default property: %r", dp, exc_info = e)
            return dp
        
        else:
            raise KeyError("Attribute for element %s not found on resource %s." % 
                           (`qname`, self.resource.fp.path))
    
    def assertExistence(self):
        """
        Raise and log an appropriate error if the resource does not exist on the file system.
        """
        if not os.path.exists(self.resource.fp.path):
            error = "Resource %s not found on file system." % self.resource.fp.path
            log.warn(error)
            raise HTTPError(StatusResponse(responsecode.NOT_FOUND, error))
    
    def remove(self):
        """
        Deletes the property store for this resource, if possible (not possible for xattr-props).
        """
        #try:
        self.store.remove()
        #except:
        #    pp = self.resource.relativePath()
        #    log.warn("Failed to remove property manager for resource: %s", pp)
        
    def set(self, element):
        
        self.assertExistence()
        
        self.store.set(element)
