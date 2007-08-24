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


import unittest
from angel_app.resource.local.basic import Basic as EResource
from angel_app.resource.local.internal.resource import Crypto

from angel_app.config import config
AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")
providerport = AngelConfig.getint("provider","listenPort")

from twisted.web2 import responsecode

import os 

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
        self.dirResource._deRegisterWithParent()  
        os.rmdir(self.testDirPath)
        
    def testDenyRemoteResourceModification(self):
        """
        Assert that all modification requests for the root resource are denied.
        For this test to run, you need a running instance of the provider.
        """
        
        from angel_app.resource.remote.clone import Clone
        
        cc = Clone()
        
        assert cc.ping(), "Test resource root unreachable."
        
        # fake resource, modification of which should be disallowed 
        dd = Clone("localhost", providerport, "/TEST")
        
        methodsAndExpectedResponseCodes = [
                                           ("MKCOL", responsecode.FORBIDDEN),
                                           ("DELETE", responsecode.FORBIDDEN),
                                           ("PUT", responsecode.FORBIDDEN),
                                           ("PROPPATCH", responsecode.FORBIDDEN),
                                           ("MOVE", responsecode.FORBIDDEN),
                                           ("COPY", responsecode.FORBIDDEN)
                                           ]
        
        for method, expect in methodsAndExpectedResponseCodes:
            response = dd._performRequest(method)
            assert response.status == expect, \
                method + " must not be allowed, received: " + `expect` + " " + response.status

