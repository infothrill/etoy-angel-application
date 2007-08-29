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
import os
from angel_app.resource.remote import client
from angel_app.resource.local import basic

from angel_app.config import config
AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

class CloneTest(unittest.TestCase):
    

    def setUp(self):
        pass

    def testPing(self):
        import socket
        oldTimeOut = socket.getdefaulttimeout()
        
        from angel_app.resource.remote.clone import Clone
        cc = Clone("80.219.195.84", 6221)
        assert False == cc.ping()
        
        dd = Clone("localhost")
        assert True == dd.ping(), "Make sure you have a local provider instance running."
        
        assert oldTimeOut == socket.getdefaulttimeout()
        
    def testInspectResource(self):
        """
        One inspection should exit happily, or raise StopIteration upon termination.
        """
        
        # look at the root, this is most often trivial.
        try:
            client.inspectResource()
        except StopIteration, e:
            pass
        assert True
        
        # look at MISSION ETERNITY
        path = os.sep.join([repositoryPath, "MISSION ETERNITY"])
        af = basic.Basic(path)
        if not os.path.exists(path): 
            return
        
        try:
            client.inspectResource(path)
            assert af.verify()
        except StopIteration, e:
            pass
        assert True

        
    
