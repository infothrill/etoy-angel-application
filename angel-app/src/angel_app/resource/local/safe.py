from twisted.web2.dav.static import DAVFile
from twisted.web2 import responsecode
from twisted.web2.http import StatusResponse
from twisted.web2.http import HTTPError
from twisted.web2 import http, stream
from twisted.web2.dav.xattrprops import xattrPropertyStore
from angel_app import elements
from angel_app.log import getLogger

log = getLogger(__name__)

def forbidden(method):
    """
    This method results in a FORBIDDEN response.
    """
    error = "Denying " + method + " request."
    log.warn(error)
    raise HTTPError(StatusResponse(responsecode.FORBIDDEN, error))

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

    def preconditions_PUT(self, request):
        """
        Disallowed.
        """
        forbidden("PUT") 

    def preconditions_MKCOL(self, request):
        """
        Disallowed.
        """
        forbidden("MKCOL") 
    
    def http_DELETE(self, request):
        """
        Disallowed.
        """
        forbidden("DELETE") 

    def http_COPY(self, request):
        """
        Disallowed.
        """
        forbidden("COPY")
    
    def http_LOCK(self, request):
        """
        Disallowed.
        """
        forbidden("LOCK")

    def http_MOVE(self, request):
        """
        Disallowed.
        """
        forbidden("MOVE") 
    
    def http_PROPPATCH(self, request):
        """
        Disallowed.
        """
        forbidden("PROPPATCH") 
           
    def http_UNLOCK(self, request):
        """
        Disallowed.
        """
        forbidden("UNLOCK")  