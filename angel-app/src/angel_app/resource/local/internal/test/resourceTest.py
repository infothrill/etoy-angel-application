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
from angel_app.resource.local.internal.resource import Crypto
import angel_app.resource.local.basic as bb

from angel_app.config import config
AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

import os 

class ResourceTest(unittest.TestCase):
    
    def testSigning(self):
        """
        this test assumes that the following resources that i set up by hand still exist in the
        local repository.
        """
        
        testDirPath = os.path.sep.join([repositoryPath, "MISSION ETERNITY", "TEST", "vincent", "test"])       
        
        dirResource = Crypto(testDirPath)        
        assert dirResource.exists(), "Test directory does not exist." 
        
        goodTestResourcePath = os.path.sep.join([testDirPath, "foo.txt"])
        fileResource = Crypto(goodTestResourcePath)
        

        assert fileResource.exists(), "Test file does not exist." 

        assert fileResource.verify(), "Test file is not valid."

        assert fileResource.contentSignature() == fileResource.sign()
