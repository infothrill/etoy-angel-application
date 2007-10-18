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
from angel_app.resource.local import basic
from angel_app.resource.remote import client
from angel_app.resource.remote.clone import Clone
import os
import unittest
import zope.interface.verify


AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

class ContentManagerTest(unittest.TestCase):
    

    def testInterfaceCompliance(self):
        """
        Verify interface compliance.
        """
        from angel_app.resource.remote.contentManager import ContentManager
        from angel_app.resource.IReadonlyContentManager import IReadonlyContentManager
        assert IReadonlyContentManager.implementedBy(ContentManager)
        assert zope.interface.verify.verifyClass(IReadonlyContentManager, ContentManager)
        
    def testRemoteStream(self):
        """
        The default clone is the root on localhost which must render to REPR_DIRECTORY
        """
        assert Clone().ping(), "locally running provider instance required"
        from angel_app.resource.abstractContentManager import REPR_DIRECTORY
        assert REPR_DIRECTORY == Clone().open().read()   
    
