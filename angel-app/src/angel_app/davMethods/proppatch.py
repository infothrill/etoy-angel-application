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

from twisted.python import log
from twisted.web2.dav.util import davXMLFromStream
from twisted.web2.dav import davxml
from twisted.internet.defer import deferredGenerator, waitForDeferred
from angel_app import elements

class ProppatchMixin:
    
    def __proppatchPreconditions(self, request):
        
        if not self.fp.exists():
            log.err("File not found: %s" % (self.fp.path,))
            raise HTTPError(responsecode.NOT_FOUND)
        
        yield request
    
    def preconditions_PROPPATCH(self, request):
        return deferredGenerator(self.__proppatchPreconditions)(request)

    def authenticate(self, requestProperties):
        """
        A PROPPATCH request is accepted exactly if the signable meta data and 
        the corresponding signature match.
        """
        sig = requestProperties[elements.MetaDataSignature.name]
        keyString = requestProperties[elements.PublicKeyString.name]
        signable = "".join([
                    requestProperties[key]
                    for key in elements.requiredKeys
                    ])
        #sm = "".join([requestProperties.childOfType(key) for key in elements.requiredKeys])
        #sm = "".join(requestProperties[1])
        log.err(sm)
        #sig = requestProperties.childOfType(elements.MetaDataSignature)
        log.err(sig)
        pubKey = key()
        pubKey.importKey(keyString)
        isValid = pubKey.verifyString(sm, sig)
        log.err(isValid)
        return isValid
        
            

    def apply(self, requestProperties, uri):

        responses = PropertyStatusResponseQueue(
                                    "PROPPATCH", 
                                    request.uri, 
                                    responsecode.NO_CONTENT)
        
        dp = self.deadProperties()
        
        for prop in requestProperties:
            try:
                dp.set(prop)
            except ValueError, err:
                responses.add(
                        Failure(
                            exc_value=HTTPError(
                                StatusResponse(
                                   responsecode.FORBIDDEN, str(e)))),
                        property
                    )
            except:
                responses.add(Failure(), property)
            else:
                responses.add(responsecode.OK, property)
            
        return responses


    def __proppatch(self, request):
        
        # read the body
        doc = waitForDeferred(deferredGenerator(readRequestBody)(request))
        yield doc
        doc = doc.getResult()
        
        # perform basic validation
        validateBodyXML(doc)
        
        # extract the properties to be patched
        requestProperties = getRequestProperties(doc)
        
        # authenticate
        self.authenticate(requestProperties)
        
        # apply the changes
        yield self.apply(requestProperties)

        
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
        log.err("Error while handling PROPPATCH body: %s" % (e,))
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, str(e)))

    if doc is None:
        error = "Request XML body is required."
        log.err(error)
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))

    yield doc

def getRequestProperties(doc):
    """
    We assume that doc has alredy been validated via validateBodyXML.
    """
    
    # get the contents of all the prop elements
    childList = [
                 child.children[0].children[0]
                 for child in doc.root_element.children
                 ]
            
    for child in childList:
            log.err(child.name)
            
    return dict([
                 (child.name, child)
                 for child in childList
                 ])

def validateBodyXML(doc):
    """
    Parse request
    """
    update = doc.root_element
    if not isinstance(update, davxml.PropertyUpdate):
        error = ("Request XML body must be a propertyupdate element."
                 % (davxml.PropertyUpdate.sname(),))
        log.err(error)
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
    
    for child in update.children:
        
        if not isinstance(child, davxml.Set):
            error = "We don't currently allow property removal via proppatch. Only SET tags are allowed."
            raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
        
        if not len(child.children) == 1:
            error = "All SET tags must contain exactly one PropertyContainer tag."
            raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
        
        if not isinstance(child.children[0], davxml.PropertyContainer):
            error = "All SET tags must contain exactly one PropertyContainer tag."
            raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, error))
