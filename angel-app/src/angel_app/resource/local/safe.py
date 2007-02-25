from twisted.web2.dav.static import DAVFile
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError
from twisted.web2 import http, stream
from twisted.web2.dav.xattrprops import xattrPropertyStore
from angel_app import elements
from angel_app.log import getLogger

log = getLogger("safe")
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
        try:
            return self.fp.path == other.fp.path
        except: return False

    def davComplianceClasses(self):
        """
        Level 2 compliance implies support for LOCK, UNLOCK
        """
        return ("1", "2")

    def precondition_MKCOL(self, request):
        """
        Disallowed.
        """
        log.warn("Denying MKCOL request.")
        return responsecode.FORBIDDEN
    
    def http_DELETE(self, request):
        """
        Disallowed.
        """
        log.warn("Denying DELETE request.")
        return responsecode.FORBIDDEN

    def http_COPY(self, request):
        """
        Disallowed.
        """
        log.warn("Denying COPY request.")
        return responsecode.FORBIDDEN
    
    def http_LOCK(self, request):
        """
        Disallowed.
        """
        log.warn("Denying LOCK request.")
        return responsecode.FORBIDDEN  

    def http_MOVE(self, request):
        """
        Disallowed.
        """
        log.warn("Denying MOVE request.")
        return responsecode.FORBIDDEN  
    
    def http_PROPPATCH(self, request):
        """
        Disallowed.
        """
        log.warn("Denying PROPPATCH request.")
        return responsecode.FORBIDDEN  
           
    def http_UNLOCK(self, request):
        """
        Disallowed.
        """
        log.warn("Denying UNLOCK request.")
        return responsecode.FORBIDDEN  