import os, urllib
from urlparse import urlsplit
from twisted.python.failure import Failure
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse
from twisted.web2.dav.http import ResponseQueue, statusForFailure
from angel_app import elements
from angel_app.resource.local.internal.util import inspectWithResponse
from angel_app.log import getLogger

log = getLogger("delete")
DEBUG = True

class Deletable(object):
    """
    A mixin class (for AngelFile) that implements deletion operations.
    """
    
    def http_DELETE(self, request):
        """
        Respond to a DELETE request. (RFC 2518, section 8.6)
        """
        DEBUG and log.debug("http_DELETE starting ")

        foo = self.delete(
                       request.uri, 
                       request.headers.getHeader("depth", "infinity")
                       )
        
        inspectWithResponse(self)(foo)
        DEBUG and log.debug("http_DELETE: " + `type(foo)`)
        return foo

