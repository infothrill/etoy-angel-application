from angel_app import elements
from angel_app.config import config
from angel_app.contrib.ezPyCrypto import key as ezKey
from angel_app.log import getLogger
from angel_app.resource.local import util
from angel_app.resource.local.contentManager import ContentManager
from angel_app.resource.local.dirlist import DirectoryLister
from angel_app.resource.local.propertyManager import PropertyManager
from angel_app.resource.local.renderManager import RenderManager
from angel_app.resource.resource import Resource
from twisted.python.filepath import FilePath
from twisted.web2 import http, stream
from twisted.web2 import responsecode
from twisted.web2.dav import davxml
from twisted.web2.dav.element import rfc2518
from twisted.web2.dav.static import DAVFile
from twisted.web2.http import HTTPError
from zope.interface import implements
import StringIO
import os
import urllib


log = getLogger(__name__)

# get config:
AngelConfig = config.getConfig()
repository = FilePath(AngelConfig.get("common","repository"))

class Basic(DAVFile, Resource):
    """
    Inheritance scheme: Resource provides high-level angel-app resource compliance,
    DAVFile provides most http_METHODS.
    """
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        DAVFile.__init__(self, path, defaultType, indexNames)
        
        # disallow the creation of resources outside of the repository
        self.assertInRepository()
        
        self._dead_properties = PropertyManager(self)
        
        self.contentManager = ContentManager(self)
        self.renderManager = RenderManager(self)
        
    def getPropertyManager(self):
        return self.deadProperties()
    
    def getContentManager(self):
        return self.contentManager
    
    def resourceName(self):
        """    
        @return the "file name" of the resource, return "/" for the repository root
        """
        if self.isRepositoryRoot(): 
            return os.sep
        else: 
            return self.fp.segmentsFrom(repository)[-1]
    
    def referenced(self):
        """
        Returns true if the resource is referenced by the parent resource.
        """
        return self.getChildElement() in self.parent().childLinks()
    
    def exists(self):
        """
        @rtype boolean
        @return true, if the corresponding file exists. If the resource is not the root resource, it must additionally be
            referenced by the parent collection.
        """   
        if not os.path.exists(self.fp.path): 

            return False 

        if not self.isRepositoryRoot(): 
            return self.referenced()
        else:
            return True

    def garbageCollect(self):
        """
        @rtype boolean
        @return true if the resource was deleted, false otherwise
        """
        if self.isRepositoryRoot():
            # the root is never referenced
            return False
        
        if os.path.exists(self.fp.path) and not self.exists():
            log.info(self.fp.path + " not referenced by parent, deleting")
            self.remove()
            return True
        else:
            return False
        
    
    def verify(self):
        """
        DEPRECATED.
        """
        return self.validate()
            

    def relativePath(self):
        """
        Returns the relative path with respect to the repository root as an absolute path,
        i.e. ${repository}/foo becomes "/foo", for the repository itself, "/" is returned.
        """
        if self.isRepositoryRoot(): return os.sep
        path = os.sep + os.sep.join(self.fp.segmentsFrom(repository))
        if self.isCollection():
            path += os.sep
        return path
    
    def relativeURL(self):
        """
        @return: a URL-quoted representation of self.relativePath()
        """
        return urllib.pathname2url(self.relativePath())
    
    def insideRepository(self):
        """
        Returns true if the resource is located beneath the repository root. False otherwise.
        """
        return self.fp.path.find(repository.path) == 0
    
    def assertInRepository(self):
        assert self.insideRepository(), "Path (%s) lies outside of repository." % self.fp.path
    
    def isRepositoryRoot(self):
        """
        Returns true, if the resource is the repository's root resource, false otherwise.
        """
        return self.fp.path == repository.path

    def parent(self):
        """
        @return this resource's parent. if this resource is the repository root, return None.
        Fail, if the resource is not located inside the repository.
        """
        self.assertInRepository()
        
        if self.isRepositoryRoot():
            # this is the root directory, don't return a parent
            return None
        
        return self.createSimilarFile( 
                                  self.fp.parent().path
                                  )

    def getChildElement(self):
        """
        @return the child element for this resource.
        """
        return elements.Child(*[
                         rfc2518.HRef(urllib.quote(self.resourceName())),
                         elements.UUID(str(self.keyUUID())),
                         self.resourceID()
                         ])

    def render(self, req):
        """You know what you doing. override render method (for GET) in twisted.web2.static.py"""
        return self.renderManager.render(req)
