##
# Copyright (c) 2005-2006 etoy.VENTURE ASSOCIATION, Inc. All rights reserved.
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
# Vincent Kraeutler, vincent@etoy.com
##

"""
WebDAV PROPPATCH method.
"""

__all__ = ["http_PROPPATCH"]

from twisted.python.failure import Failure
from twisted.web2 import responsecode
from twisted.web2.http import HTTPError, StatusResponse
from twisted.web2.dav.util import davXMLFromStream
from twisted.web2.dav import davxml
from twisted.web2.dav.http import MultiStatusResponse, PropertyStatusResponseQueue
from twisted.internet.defer import deferredGenerator, waitForDeferred
from angel_app import elements
from angel_app.log import getLogger
import os

log = getLogger(__name__)


# get config:
from angel_app.config import config
AngelConfig = config.getConfig()
maxclones = AngelConfig.getint("common","maxclones")


class ProppatchMixin:
    
    def preconditions_PROPPATCH(self, request):
        
        if not os.path.exists(self.fp.path):
            error = "File not found: %s" % (self.fp.path,)
            log.error(error)
            raise HTTPError(StatusResponse(
                       responsecode.NOT_FOUND, error))

    def apply(self, requestProperties, request):
        """
        @param requestProperties: properties to be applied
        @param request: the request object
        @return a MULTISTATUS response object containing the response for each request property.
                
        we're being overly general here -- i.e. handling of multiple property responses
        when we know from previous validation that only one property may be supplied.
        however, this code works, so we might as well keep it.
        """
        responses = PropertyStatusResponseQueue(
                                    "PROPPATCH", 
                                    request.uri, 
                                    responsecode.NO_CONTENT)
        
        dp = self.deadProperties()

        propertyResponses = [(property, cloneHandler(property, dp, request))
                             for property in requestProperties]
        
        for (property, response) in propertyResponses:
            responses.add(response, property)
        
        return MultiStatusResponse([responses.response()])


    def __proppatch(self, request):
        
        # read the body
        doc = waitForDeferred(deferredGenerator(readRequestBody)(request))
        yield doc
        doc = doc.getResult()
        
        # perform basic validation, and extract the clone field to be updated
        try:
            cloneField = validateBodyXML(doc)
        except AssertionError, e:
            error = "PROPPATCH request body does not validate. Error: " + str(e)
            log.info(error)
            raise HTTPError(StatusResponse(responsecode.FORBIDDEN, error))
        
        # apply the changes
        yield self.apply([cloneField], request)

        
    def http_PROPPATCH(self, request):
        return deferredGenerator(self.__proppatch)(request)


def readRequestBody(request):
    """
    Read XML body from request stream.
    """
    try:
        doc = waitForDeferred(davXMLFromStream(request.stream))
        yield doc
        doc = doc.getResult()
    except ValueError, e:
        log.error("Error while reading PROPPATCH body: %s" % (e,))
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, str(e)))

    if doc is None:
        error = "Request XML body is required."
        log.error(error)
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
    else:
        yield doc

def validateBodyXML(doc):
    """
    Perform syntactical validation of the request body.
    @param doc: the request body as a davxml document. 
    """
    assert isinstance(doc.root_element, davxml.PropertyUpdate), \
        "Request XML body must be a propertyupdate element. Found: " + `update.sname()`
    
    assert 1 == len(doc.root_element.children), "Only one PROPPATCH instruction allowed."
    
    child = doc.root_element.children[0]
        
    assert isinstance(child, davxml.Set), \
        "The PROPPATCH instruction must be a SET instruction. Found: " + `child.sname()`
        
    assert (1 == len(child.children) and isinstance(child.children[0], davxml.PropertyContainer)), \
            "All SET tags must contain exactly one PropertyContainer tag."
        
    propertyContainer = child.children[0]
    assert (1 == len(propertyContainer.children) and isinstance(propertyContainer.children[0], elements.Clones)), \
        "The property container must contain exactly one clones element."
    
    clones = propertyContainer.children[0]
    assert (1 == len(clones.children) and isinstance(clones.children[0], elements.Clone)), \
        "The Clones element must contain exactly one clone element."
    
    # return the clone element
    return propertyContainer.children[0]
                
def defaultHandler(property, store):
    """
    Add an individual property.
    
    @param property: the property to be stored
    @param store: where to store the property
    @return: the response for this property
    """
    try:
        if store.contains(property.qname()) and (store.get(property.qname()) == property):
            pass
        else:
            store.set(property)
        return responsecode.OK

    except ValueError, err:
        return Failure(exc_value=HTTPError(
                                StatusResponse(
                                   responsecode.BAD_REQUEST, str(err))))
                
def cloneHandler(property, store, request):
    """
    The host from which the request originates must have access to a local clone,
    store if we want.
    """
    from angel_app.resource.remote.clone import clonesFromElement, clonesToElement
    if store.contains(elements.Clones.qname()):
        residentClones = clonesFromElement(store.get(elements.Clones.qname()))
    else:
        residentClones = []
        
    if len(residentClones) >= maxclones: 
        error = "Too many clones. Not adding."
        log.info(error)
        response = StatusResponse(responsecode.BAD_REQUEST, error)
        return Failure(exc_value=HTTPError(response))
            
    address = str(request.remoteAddr.host)
    try:
        newClone = clonesFromElement(property)[0]
        newClone.host = address
       
    except Exception, e:
        log.warn("received malformed clone:" + `property` + "from host:" + `address` + ". Error: \n" + `e`)
        response = StatusResponse(responsecode.BAD_REQUEST, error)
        return Failure(exc_value=HTTPError(response))
            
    return defaultHandler(clonesToElement(residentClones + [newClone]), store)     

            
            # up until revision 572, there was some validation code in here, that would check
            # back on the source clone to verify its existence and reachability. this leads
            # to spurious hangs, since the source of the proppatch may (and will) be the provider
            # process on the local host -- in which case we have reached a deadlock. the code
            # has therefore been removed.