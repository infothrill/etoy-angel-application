import os, urllib

from twisted.python.failure import Failure
from twisted.web2 import responsecode
from twisted.web2.dav.http import ResponseQueue
from twisted.web2.http import HTTPError, StatusResponse
from urlparse import urlsplit
#from angel_app.resource.local.internal import resource

from angel_app.log import getLogger
log = getLogger(__name__)

class Deletable(object):
    """
    A mixin class (for AngelFile) that implements deletion operations.
    """
    
    #def http_DELETE(self, request):
    #    self._deRegisterWithParent()
    #    return super(Deletable, self).http_DELETE(request)
    
    def http_DELETE(self, request):
        """
        Respond to a DELETE request. (RFC 2518, section 8.6)
        """
        self.remove()
        return responsecode.NO_CONTENT

    def preconditions_DELETE(self, request):

        checkDepthHeader(request)
    
        if not self.exists():
            log.debug("File not found: %s" % (self.fp.path,))
            raise HTTPError(responsecode.NOT_FOUND)
        
        if not self.isWritableFile():
            log.debug("Not authorized to delete file: %s" % (self.fp.path,))
            raise HTTPError(responsecode.UNAUTHORIZED)



def checkDepthHeader(request):
        """
        RFC 2518, section 8.6 says that we must act as if the Depth header is
        set to infinity, and that the client must omit the Depth header or set
        it to infinity, meaning that for collections, we will delete all
        members.
        
        This seems somewhat at odds with the notion that a bad request should
        be rejected outright; if the client sends a bad depth header, the
        client is broken, and RFC 2518, section 8 suggests that a bad request
        should be rejected...
        
        Let's play it safe for now and ignore broken clients.
        """
        depth = request.headers.getHeader("depth", "infinity")
        if depth != "infinity":
            msg = ("Client sent illegal depth header value for DELETE: %s" % (depth,))
            log.debug(msg)
            raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, msg))
