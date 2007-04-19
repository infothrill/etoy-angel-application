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
import angel_app.contrib.ezPyCrypto
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
            log.error("File not found: %s" % (self.fp.path,))
            raise HTTPError(responsecode.NOT_FOUND)

    def authenticate(self, request, requestProperties):
        """
        A PROPPATCH request is accepted exactly if the signable meta data and 
        the corresponding signature match, and the public key of the request is
        the same as the public key of the local resource.
        """
        
        def __get(element):
            return requestProperties[element.name]
        
        def __string(strings):
            return "".join([str(ss) for ss in strings])
        
        def __both(element):
            return __string(__get(element).children)
        
        def __xml(element):
            return __get(element).toxml()
        
        try: 
            lid = self.resourceID()
        except:
            # TODO: review -- this is a potential security hole if not handled right,
            # but we are going to be careful, aren't we?
            return True
        rid = __get(elements.ResourceID)
        if not lid == rid:
            log.info("resource ID's for PROPPATCH don't match. Local: %s, remote: %s" % (lid, rid))
            return False
        
        sig = __both(elements.MetaDataSignature)
        keyString = __both(elements.PublicKeyString)
        
        if keyString != self.publicKeyString():
            error = "denied attempt to PROPPATCH %s with wrong key from host %s " % \
                (self.fp.path, str(request.remoteAddr.host))
            log.info(error)
            raise HTTPError(StatusResponse(
                                   responsecode.UNAUTHORIZED, error))
        
        signable = __string([
                     __xml(element)
                    for element in elements.signedKeys
                    ])

        log.debug("PROPPATCH: signable:" + `signable`)
        pubKey = angel_app.contrib.ezPyCrypto.key()
        pubKey.importKey(keyString)
        isValid = pubKey.verifyString(signable, sig)
        log.debug("PROPPATCH request signature is valid: " + `isValid`)
        return isValid
        
            

    def apply(self, requestProperties, request, uri):

        responses = PropertyStatusResponseQueue(
                                    "PROPPATCH", 
                                    uri, 
                                    responsecode.NO_CONTENT)
        
        dp = self.deadProperties()
        
        def defaultHandler(property, store, responses):
            try:
                if store.contains(property.qname()) and (store.get(property.qname()) == property):
                    log.debug("Supplied property: %s identical to available property: %s. Not updating resource."
                              % (property.toxml(), store.get(property.qname()))
                              )
                else:
                    log.debug("storing property: " + `property`)
                    store.set(property)

            except ValueError, err:
                log.error("Failed to add property " + `property` + ". Failed with error :" + err)
                responses.add(
                        Failure(
                            exc_value=HTTPError(
                                StatusResponse(
                                   responsecode.BAD_REQUEST, str(err)))),
                        property
                    )
                
        def cloneHandler(property, store, request, responses):
            """
            The host from which the request originates must have access to a local clone,
            store if we want.
            """
            from angel_app.resource.remote.clone import clonesFromElement, clonesToElement
            try:
                residentClones = clonesFromElement(dp.get(elements.Clones))
            except:
                residentClones = []
            if len(residentClones) >= maxclones: return
            
            address = str(request.remoteAddr.host)
            try:
                newClone = clonesFromElement(property)[0]
                newClone.host = address
       
            except:
                log.warn("received malformed clone:" + `property` + "from host:" + `address`)
                return
            
            log.info("adding clone: " + `newClone` + " to resource " + self.fp.path)   
            defaultHandler(clonesToElement(residentClones + [newClone]), store, responses)     

            
            # up until revision 572, there was some validation code in here, that would check
            # back on the source clone to verify its existence and reachability. this leads
            # to spurious hangs, since the source of the proppatch may (and will) be the provider
            # process on the local host -- in which case we have reached a deadlock. the code
            # has therefore been removed.
            
        
        for property in requestProperties:
            log.debug("proppatch applying: " + property.toxml())
            log.debug("proppatch applying: " + `property.__class__`)
            try:
                if property.__class__ == elements.Clones:
                    cloneHandler(property, dp, request, responses)
                    log.debug("OK")
                elif property.__class__ in elements.requiredKeys:
                    defaultHandler(property, dp, responses)
                    log.debug("OK")
                else: # we don't generally accept unsigned material
                    responses.add(responsecode.UNAUTHORIZED, property)
                    log.debug("UNAUTHORIZED")
            except:
                responses.add(Failure(), property)
            else:
                responses.add(responsecode.OK, property)
      
        # remove all unreferenced children
        self.familyPlanning()
        
        return MultiStatusResponse([responses.response()])


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
        isValid = self.authenticate(request, requestProperties)
        if not isValid:
            raise HTTPError(StatusResponse(
                       responsecode.FORBIDDEN, "The PROPPATCH certificate is not valid."))
        
        # apply the changes
        yield self.apply(requestProperties.values(), request, request.uri)


        
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
        log.error("Error while handling PROPPATCH body: %s" % (e,))
        raise HTTPError(StatusResponse(responsecode.BAD_REQUEST, str(e)))

    if doc is None:
        error = "Request XML body is required."
        log.error(error)
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
            log.info(child.name)
            
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
        log.error(error)
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
