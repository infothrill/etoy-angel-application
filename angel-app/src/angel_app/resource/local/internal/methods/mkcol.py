# -*- test-case-name: twisted.web2.dav.test.test_mkcol -*-
##
# Copyright (c) 2005 Apple Computer, Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# DRI: Wilfredo Sanchez, wsanchez@apple.com
##

"""
WebDAV MKCOL method
"""

__all__ = ["http_MKCOL"]

import os
from logging import getLogger

from twisted.internet.defer import deferredGenerator, waitForDeferred
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse
from twisted.web2.dav.fileop import mkcollection
from twisted.web2.dav.util import noDataFromStream
#from angel_app import elements
#from angel_app.resource.local.internal.util import inspectWithResponse

log = getLogger(__name__)

class mkcolMixin:

    def __checkSpot(self):

        log.debug("calling __checkSpot")

        if os.path.exists(self.fp.path):
            log.warn("Attempt to create collection where resource exists: %s"
                % (self.fp.path,))
            raise HTTPError(responsecode.NOT_ALLOWED)

        if not self.parent().isCollection():
            log.error("Attempt to create collection with non-collection parent: %s"
                % (self.parent().fp.path,))
            raise HTTPError(StatusResponse(
                                           responsecode.CONFLICT,
                "Parent resource is not a collection."
                ))

        if not self.parent() or not self.parent().isCollection():
            log.error("Attempt to create collection with no parent directory: %s"
                % (self.fp.path,))
            raise HTTPError(StatusResponse(
                                           responsecode.INTERNAL_SERVER_ERROR,
            "The requested resource is not backed by a parent directory."
            ))
      
        if not self.parent().isWritableFile():
            errorMessage = "You don't have sufficient privileges to create a collection in this location."
            log.error(errorMessage)
            raise HTTPError(StatusResponse(responsecode.UNAUTHORIZED, errorMessage))
          
        log.debug("done __checkSpot")
        

    def __mkcol(self, request):
    
        self.__checkSpot()

        #
        # Read request body
        #
        x = waitForDeferred(noDataFromStream(request.stream))
        yield x
        try:
            x.getResult()
        except ValueError, e:
            log.error("Error while handling MKCOL body: %s" % (e,))
            raise HTTPError(responsecode.UNSUPPORTED_MEDIA_TYPE)

        ignored = waitForDeferred(mkcollection(self.fp))  
        yield ignored
        ignored = ignored.getResult()

        log.debug("__mkcol registering with parent")
        self._registerWithParent()
    
        log.debug("__mkcol updating metadata")
        self._updateMetadata()
    
        log.debug("done MKCOL request")   
        yield responsecode.CREATED

    def http_MKCOL(self, request):
        """
        Respond to a MKCOL request. (RFC 2518, section 8.3)
        """     
    
        return deferredGenerator(self.__mkcol)(request)#.addCallback(inspectWithResponse(self))
