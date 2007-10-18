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

from angel_app.config import config
from angel_app.log import getLogger
from angel_app.resource.local.basic import Basic as EResource
from angel_app.resource.local.internal.resource import Crypto
from angel_app.resource.local.internal.resource import Crypto as IResource
from angel_app.resource.local.test import localResourceTest
from angel_app.resource.remote.clone import Clone
from twisted.web2 import responsecode
import angel_app.resource.local.basic as bb
import os 


AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

log = getLogger(__name__)


class ResourceTest(localResourceTest.BasicResourceTest):
    """
    Requires a running local instance of the presenter.
    """
    
    testDirPath = os.path.sep.join([repositoryPath, "TEST"])
    testClone = Clone(
                      host = "localhost", 
                      port = AngelConfig.getint("presenter","listenPort"),
                      path = "/TEST")
    

    def setUp(self):
        try:
            os.mkdir(self.testDirPath)
        except OSError, e:
            # test resource already exists
            pass
        self.dirResource = Crypto(self.testDirPath) 
        self.dirResource._registerWithParent()  
        self.dirResource._updateMetadata()
        
    def tearDown(self):
        self.dirResource._deRegisterWithParent()
        try:
            os.rmdir(self.testDirPath)
        except:
            pass
    
    def testSigning(self):
        """
        this test assumes that the following resources that i set up by hand still exist in the
        local repository.
        """    
        
        dirResource = Crypto(self.testDirPath)        
        assert dirResource.exists(), "Test directory does not exist." 
        assert dirResource.verify(), "Test directory is not valid."
        assert dirResource.contentSignature() == dirResource.sign()
        
    def testDenyRemoteResourceModification(self):
        """
        Assert that all modification requests for the root resource are denied.
        For this test to run, you need a running instance of the provider.
        
        Consider using the litmus test suite for in-depth testing.
        """
        
        assert self.testClone.ping(), \
            "Test resource unreachable. Make sure you have a running instance of the presenter."
        
        methodsAndExpectedResponseCodes = [
                                           # first, we make a collection -- this should fail, because it already exists
                                           ("MKCOL", responsecode.NOT_ALLOWED),
                                           
                                           # next, we attempt to overwrite the collection with an empty file
                                           ("PUT", responsecode.FORBIDDEN),
                                           
                                           # next, we send a malformed proppatch request,
                                           ("PROPPATCH", responsecode.BAD_REQUEST),
                                           
                                           # move and copy the resource without a destination:
                                           ("MOVE", responsecode.BAD_REQUEST),
                                           ("COPY", responsecode.BAD_REQUEST),
                                           
                                           # delete the resource
                                           ("DELETE", responsecode.NO_CONTENT),
                                           
                                           # create the original collection
                                           ("MKCOL", responsecode.CREATED),
                                           ]
        
        for method, expect in methodsAndExpectedResponseCodes:
            response = self.testClone.remote.performRequest(method)
            assert response.status == expect, \
                method + " wrong status code returned. expected: " + `expect` + " found: " + `response.status`
