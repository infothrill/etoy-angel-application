from twisted.web2.dav.static import DAVFile
from twisted.python import log
from twisted.web2 import responsecode, dirlist
from twisted.web2.http import HTTPError
from twisted.web2 import http, stream
from twisted.web2.dav.xattrprops import xattrPropertyStore
from angel_app import elements
from angel_app.davMethods.lock import Lockable
from angel_app.davMethods.proppatch import ProppatchMixin

DEBUG = False

class Safe(DAVFile):
    """
    This implements a safe WebDAV resource, in that all requests to modifiy
    this resource are denied.
    """
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        DAVFile.__init__(self, path, defaultType, indexNames)
        
    def __eq__(self, other):
        return self.fp.path == other.fp.path  

    def davComplianceClasses(self):
        """
        Level 2 compliance implies support for LOCK, UNLOCK
        """
        return ("1", "2")

    def http_MKCOL(self, request):
        """
        Disallowed.
        """
        log.err("Denying MKCOL request.")
        return responsecode.FORBIDDEN
    
    def http_DELETE(self, request):
        """
        Disallowed.
        """
        log.err("Denying DELETE request.")
        return responsecode.FORBIDDEN

    def http_COPY(self, request):
        """
        Disallowed.
        """
        log.err("Denying COPY request.")
        return responsecode.FORBIDDEN
    
    def http_LOCK(self, request):
        """
        Disallowed.
        """
        log.err("Denying LOCK request.")
        return responsecode.FORBIDDEN  

    def http_MOVE(self, request):
        """
        Disallowed.
        """
        log.err("Denying MOVE request.")
        return responsecode.FORBIDDEN  
    
    def http_PROPPATCH(self, request):
        """
        Disallowed.
        """
        log.err("Denying PROPPATCH request.")
        return responsecode.FORBIDDEN  
           
    def http_UNLOCK(self, request):
        """
        Disallowed.
        """
        log.err("Denying UNLOCK request.")
        return responsecode.FORBIDDEN  