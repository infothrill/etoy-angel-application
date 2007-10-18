"""
Tests for local resource.
"""

legalMatters = """
 Copyright (c) 2006, etoy.VENTURE ASSOCIATION
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without modification, 
 are permitted provided that the following conditions are met:
 *  Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.
 *  Redistributions in binary form must reproduce the above copyright notice, 
    this list of conditions and the following disclaimer in the documentation 
    and/or other materials provided with the distribution.
 *  Neither the name of etoy.CORPORATION nor the names of its contributors may be used to 
    endorse or promote products derived from this software without specific prior 
    written permission.
 
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
 EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
 OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
 SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT 
 OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
 OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
"""

author = """Vincent Kraeutler 2007"""


from angel_app import elements
from angel_app.config import config
from angel_app.resource.local.basic import Basic as EResource
from angel_app.resource.local.internal.resource import Crypto
from angel_app.resource.remote import clone
from twisted.web2 import responsecode
from twisted.web2.dav.element import rfc2518
import os 
import unittest


AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")
providerport = AngelConfig.getint("provider","listenPort")

           
def makePushBody(localClone, elements = elements.requiredKeys):
    """
    Generate the DAVDocument representation of the required properties of the local clone.
    """
    
    def makeSetElement(elements):
        return rfc2518.Set(
                         rfc2518.PropertyContainer(element))
        
    cc = clone.Clone("localhost", providerport, localClone.relativeURL())
    pList = [makeSetElement(element) for element in
             [localClone.deadProperties().get(el.qname()) for el in elements]
              + [clone.clonesToElement([cc])]]
    
    pu = rfc2518.PropertyUpdate(*pList)
    return pu.toxml()

def performPushRequest(self, localClone, elements = elements.requiredKeys):
    """
    Push the relevant properties of a local clone to the remote clone via a PROPPATCH request.
    @param elements is a list of property elements we want to push out to the remote clone
    """
    pb = makePushBody(localClone, elements)
    log.debug("pushing metadata:" + pb + " for clone " + `self`)
    resp = self.remote.performRequest(
                                     method = "PROPPATCH", 
                                     body = pb
                                     )
    # we probably ignore the returned data, but who knows
    data = resp.read()
    if resp.status != responsecode.MULTI_STATUS:
        if resp.status == responsecode.NOT_FOUND:
            raise CloneNotFoundError("Clone %s not found, response code is: %s, data is %s" % (`self`, `resp.status`, data) )
        else:
            raise CloneError("must receive a MULTI_STATUS response for PROPPATCH, otherwise something's wrong, got: " + `resp.status` +\
                    data)

def runRequest(clone, method, expect):
    response = clone.remote.performRequest(method)
    assert response.status == expect, \
        method + " -- got wrong status code, expected: " + `expect` + " received: " + `response.status` + "\n" + \
        response.read()

class ForbiddenTest(unittest.TestCase):
    """
    I make sure that all destructive method calls are forbidden on the external interface.
    """
    
    testDirPath = os.path.sep.join([repositoryPath, "TEST"])

    def setUp(self):
        try:
            os.mkdir(self.testDirPath)
        except:
            pass
        self.dirResource = Crypto(self.testDirPath) 
        self.dirResource._registerWithParent()  
        self.dirResource._updateMetadata()
        
    def tearDown(self):
        self.dirResource.remove()
        
    def testDenyRemoteResourceModification(self):
        """
        Assert (except for PROPPATCH) that all modification requests for the root resource are denied.
        For this test to run, you need a running instance of the provider.
        """
        
        from angel_app.resource.remote.clone import Clone
        
        # fake resource, modification of which should be disallowed 
        dd = Clone("localhost", providerport, "/TEST")
        assert dd.ping(), "Test resource root unreachable."
        
        methodsAndExpectedResponseCodes = [
                                           ("MKCOL", responsecode.FORBIDDEN),
                                           ("DELETE", responsecode.FORBIDDEN),
                                           ("PUT", responsecode.FORBIDDEN),
                                           ("MOVE", responsecode.FORBIDDEN),
                                           ("COPY", responsecode.FORBIDDEN)
                                           ]
        
        for method, expect in methodsAndExpectedResponseCodes:
            runRequest(dd, method, expect)

        
    def testAllowRemoteResourceRead(self):
        """
        Perform read-only requests on remote resource
        """
        
        from angel_app.resource.remote.clone import Clone
        
        # fake resource, modification of which should be disallowed 
        dd = Clone("localhost", providerport, "/TEST/")
        assert dd.ping(), "Test resource root unreachable. Make sure you have a provider instance running."
        assert self.dirResource.exists()
        
        methodsAndExpectedResponseCodes = [
                                           ("GET", responsecode.OK),
                                           ("PROPFIND", responsecode.MULTI_STATUS),
                                           ]
        
        for method, expect in methodsAndExpectedResponseCodes:
            runRequest(dd, method, expect)


    def testCollectionRedirect(self):
        """
        path without trailing backslash affords redirect for directories
        """
                
        from angel_app.resource.remote.clone import Clone
        
        dd = Clone("localhost", providerport, "/TEST")
        
        methodsAndExpectedResponseCodes = [("GET", responsecode.MOVED_PERMANENTLY)]
        
        for method, expect in methodsAndExpectedResponseCodes:
            runRequest(dd, method, expect)

    def testProppatch(self):
        """
        Assert (except for PROPPATCH) that all modification requests for the root resource are denied.
        For this test to run, you need a running instance of the provider.
        """

        
        # fake resource, modification of which should be disallowed 
        dd = clone.Clone("localhost", providerport, "/TEST")
        
        assert dd.ping(), "Test resource root unreachable. Make sure you have a running provider instance."
        
        method = "PROPPATCH"
        
        response = dd.remote.performRequest(method)
        assert (response.status == responsecode.BAD_REQUEST), \
            "Request with empty body must fail with 400 BAD_REQUEST. Received: " + `response.status`
            
        body = makePushBody(self.dirResource)
        
        response = dd.remote.performRequest(method, body = body)
        assert (response.status == responsecode.FORBIDDEN), \
            "Request with extensive property update must fail with 403 FORBIDDEN. Received: " + `response.status`
            
        body = clone.makeCloneBody(self.dirResource)
        response = dd.remote.performRequest(method, body = body)
        
        # TODO: we might want to add a detailed analysis of the MULTI_STATUS response here.
        assert (response.status == responsecode.MULTI_STATUS), \
            "Request with well-formed property update must succeed with MULTI_STATUS response. Received: " + `response.status`

