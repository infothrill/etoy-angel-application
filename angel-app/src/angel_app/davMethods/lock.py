# -*- test-case-name: twisted.web2.dav.test.test_mkcol -*-
##
# Copyright (c) 2005 Apple Computer, Inc. All rights reserved.
# Copyright (c) 2006 etoy.CORPORATION, AG. All rights reserved.
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
WebDAV LOCK method
"""

__all__ = ["http_LOCK"]

from twisted.python import log
from twisted.internet.defer import deferredGenerator
from twisted.internet.defer import waitForDeferred
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse
from twisted.web2.dav.http import MultiStatusResponse
from twisted.web2.dav import davxml
from twisted.web2.dav.util import davXMLFromStream

def contentHandlerFromLockXML(request):
    """
    parse an xml request body. yields a WebDAVContentHandler (?).
    """

    try:
        doc = waitForDeferred(davXMLFromStream(request.stream))
        yield doc
        doc = doc.getResult()
    except ValueError, e:
        log.err("Error while handling LOCK body: %s" % (e,))
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, str(e)))
    
    if doc is None:
        # No request body makes no sense
        error = ("Empty LOCK request.")
        log.err(error)
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
    
    log.err(type(doc))
    yield doc

def getChildOfType(elementNode, itemType):
    """
    Return the first child of elementNode that is an instance of
    itemType. If no such child is found, raise an exception.
    """
    for child in elementNode.children:
        if isinstance(child, itemType):
            return child
        
    error = "Expected element of type: " + itemType.name
    raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))

def lockSpecFromContentHandler(contentHandler):
    """
    Validate lock request document.
    """
    
    root = contentHandler.root_element
    if not isinstance(root, davxml.LockInfo):
        error = ("Non-%s element in LOCK request body: %s"
                     % (davxml.LockInfo.sname(), root))
        log.err(error)
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))

    lockScope = getChildOfType(root, davxml.LockScope)
    lockType = getChildOfType(root, davxml.LockType)
    lockOwner = getChildOfType(root, davxml.Owner)
    lockHref = getChildOfType(lockOwner, davxml.Owner)
    return {
            davxml.LockScope.name   : lockScope,
            davxml.LockType.name    : lockType,
            davxml.Owner.name       : lockOwner,
            davxml.HRef.name        : lockHref
            }

def parseLockRequest(filePath, request):
    
    # does the file exist?
    if not filePath.exists():
        log.err( "File not found in LOCK request: %s" % ( filePath.path, ) )
        raise HTTPError(responsecode.NOT_FOUND)
    
    dom = contentHandlerFromLockXML(request)
    yield dom
    dom = dom.getResult()
    
    log.err(type(dom))
    #dom = dom.next().getResult()
    #log.err(type(dom))
    #log.err(dir(dom))
    
    if not isinstance(dom.root_element, davxml.LockInfo):
        error = ("Non-%s element in LOCK request body: %s"
                     % (davxml.LockInfo.sname(), dom.root_element))
        log.err(error)
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
   
    yield lockSpecFromContentHandler(dom.root_element)



class Lockable:
    
    def __lock(self, request):
        """
        Respond to a LOCK request. (RFC 2518, section 8.10)
        """
        
        log.err( "received LOCK request for %s" % ( self.fp.path, ) )
    
        lock = parseLockRequest(self.fp, request)
        #log.err(lock)

        #
        # TODO: Generate XML output stream (do something with lock)
        #

        # vincent:
        # we should certainly return a reasonable response here
        # (for inspiration, see twisted.dav.method.propfind and RFC 2518, examples 8.10.8
        # through 8.10.10), but since i only want OS X 10.4 to be happy (and it is with
        # this), i'll stop here for now.
        yield MultiStatusResponse([])
    #def __init__(self):
    #    self.http_LOCK = deferredGenerator(self.http_LOCK)
    
    def http_LOCK(self, request):
                #return self.put(request.stream)
        return deferredGenerator(self.__lock)(request.stream)
