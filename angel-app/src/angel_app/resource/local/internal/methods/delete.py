import os, urllib
from urlparse import urlsplit
from twisted.python import log
from twisted.python.failure import Failure
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse
from twisted.web2.dav.http import ResponseQueue, statusForFailure
from angel_app import elements

DEBUG = True

class Deletable(object):
    """
    A mixin class (for AngelFile) that implements deletion operations.
    """
    
    def http_DELETE(self, request):
        """
        Respond to a DELETE request. (RFC 2518, section 8.6)
        """
        DEBUG and log.err("http_DELETE starting ")

        foo = self.delete(
                       request.uri, 
                       request.headers.getHeader("depth", "infinity")
                       )#.addCallback(inspectWithResponse)
        DEBUG and log.err("http_DELETE: " + `type(foo)`)
        return foo

