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

from twisted.python import log
from twisted.internet.defer import deferredGenerator, waitForDeferred
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse
from twisted.web2.dav.fileop import mkcollection
from twisted.web2.dav.util import noDataFromStream, parentForURL
from angel_app import elements


DEBUG = True

class mkcolMixin:

  def __checkSpot(self, parent):

    if self.fp.exists() and not self.isCollection():
        log.err("Attempt to create collection where file exists: %s"
                % (self.fp.path,))
        raise HTTPError(responsecode.NOT_ALLOWED)

    if not parent.isCollection():
        log.err("Attempt to create collection with non-collection parent: %s"
                % (parent.fp.path,))
        log.err(parent.listChildren())
        log.err(parent.fp.isdir())
        raise HTTPError(StatusResponse(
            responsecode.CONFLICT,
            "Parent resource is not a collection."
        ))

    if not self.fp.parent().isdir():
        log.err("Attempt to create collection with no parent directory: %s"
                % (self.fp.path,))
        raise HTTPError(StatusResponse(
            responsecode.INTERNAL_SERVER_ERROR,
            "The requested resource is not backed by a parent directory."
        ))
        

  def __mkcol(self, request):

    parent = waitForDeferred(request.locateResource(parentForURL(request.uri)))
    yield parent
    parent = parent.getResult()
    
    self.__checkSpot(parent)

    #
    # Read request body
    #
    x = waitForDeferred(noDataFromStream(request.stream))
    yield x
    try:
        x.getResult()
    except ValueError, e:
        log.err("Error while handling MKCOL body: %s" % (e,))
        raise HTTPError(responsecode.UNSUPPORTED_MEDIA_TYPE)

    if not self.fp.exists():
        ignored = waitForDeferred(mkcollection(self.fp))  
        yield ignored
        ignored = ignored.getResult()
    else:
        self.deadProperties().set(elements.Deleted.fromString("0"))
    


    DEBUG and log.err("updating parent for " + self.fp.path)
    parent.update()
    DEBUG and log.err("updating " + self.fp.path)
    self.update()
    
    DEBUG and log.err("done MKCOL request")   
    yield responsecode.CREATED

  def http_MKCOL(self, request):
        """
        Respond to a MKCOL request. (RFC 2518, section 8.3)
        """     
        log.err("received MKCOL request for " + self.fp.path)
    
        #return self.put(request.stream)
        return deferredGenerator(self.__mkcol)(request)
        #return self.put(request.stream)
        #put = deferredGenerator(self.put)
        #return put(request.stream)
