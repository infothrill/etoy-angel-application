from angel_app.resource.local.basic import Basic

from twisted.internet.defer import Deferred
from twisted.web2 import responsecode
from twisted.web2.http import StatusResponse
from twisted.web2.http import HTTPError

from angel_app.log import getLogger
from angel_app.resource.local.external.methods import proppatch

log = getLogger(__name__)

def forbidden(method):
    """
    This method results in a FORBIDDEN response.
    """
    error = "Denying " + method + " request."
    log.warn(error)
    raise HTTPError(StatusResponse(responsecode.FORBIDDEN, error))


class External(proppatch.ProppatchMixin, Basic):
    """
    WebDAV resource interface for provider. All destructive methods are forbidden.

    Additionally, the External resource class is responsible for inserting new clone references
    into the network. Specifically, ater a GET request has been successfully handled, a method
    is dispathced that verifies if the host from which the GET request originated is now itself
    offering a clone of that resource (see http_GET for details).
    """
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        
        Basic.__init__(self, path, defaultType, indexNames)

# forbidden method follow


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
    
    def preconditions_DELETE(self, request):
        """
        Disallowed.
        """
        forbidden("DELETE") 

    def preconditions_COPY(self, request):
        """
        Disallowed.
        """
        forbidden("COPY")
    
    def preconditions_LOCK(self, request):
        """
        Disallowed.
        """
        forbidden("LOCK")

    def preconditions_MOVE(self, request):
        """
        Disallowed.
        """
        forbidden("MOVE")  
           
    def preconditions_UNLOCK(self, request):
        """
        Disallowed.
        """
        forbidden("UNLOCK")  