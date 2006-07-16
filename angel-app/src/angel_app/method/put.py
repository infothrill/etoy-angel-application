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
WebDAV PUT method
"""

__all__ = ["http_PUT"]

from twisted.python import log
from twisted.web2.http import HTTPError
from twisted.web2 import responsecode
from twisted.internet.defer import deferredGenerator
#from twisted.web2.dav.fileop import put
from angel_app.dav.fileop import put
from angel_app.core import elements

def http_PUT(self, request):
    """
    Respond to a PUT request. (RFC 2518, section 8.7)
    """
    
    log.err("received PUT request for " + self.fp.path)   
    
    try:
        pass
    except: # the file doesn't exist (yet)
        log.err("adding new file at: " + self.fp.path)

    if not self.isWritableFile():
        log.err("http_PUT: not authorized to put file: " + self.fp.path)
        raise HTTPError(responsecode.UNAUTHORIZED)
        
    deferred = put(request.stream, self.fp) 
    # define callbacks as closures:
    
    def updateMetadata(response): 
        # if the file has been previously deleted,
        # the "deleted" flag has been set to "1"
        # undo that
        self.deadProperties().set(elements.Deleted.fromString("0"))
        self.update()
        return response 
    

    #log.err(DAVFile.http_PUT(self, request).__dict__.keys())
    #log.err(super(DAVFile, self).__dict__.keys())
    #deferred = super(DAVFile, self).http_PUT(request)
    #deferred = DAVFile.http_PUT(self, request)


               
    deferred.addCallback(updateMetadata)
      
    return deferred
