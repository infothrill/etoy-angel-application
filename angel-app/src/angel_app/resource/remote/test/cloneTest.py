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
from angel_app.resource.IResource import IAngelResource
from angel_app.resource.local import basic
from angel_app.resource.remote import client
from angel_app.resource.remote import clone
from angel_app.resource.remote.clone import Clone
import os
import unittest
import zope.interface.verify
from angel_app.resource.test import resourceTest

AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

class CloneTest(resourceTest.ResourceTest):
    

    def setUp(self):
        self.testResource = clone.Clone("localhost")
        assert self.testResource.ping(), "make sure you have a local instance of the provider running."
        self.localTestResource = basic.Basic(repositoryPath)

    def testPing(self):
        import socket
        oldTimeOut = socket.getdefaulttimeout()
        
        from angel_app.resource.remote.clone import Clone
        cc = Clone("80.219.195.84", 6221)
        assert False == cc.ping()
        
        dd = Clone("localhost")
        assert True == dd.ping(), "Make sure you have a local provider instance running."
        
        assert oldTimeOut == socket.getdefaulttimeout()
        
    def testIsCollection(self):
        
        assert self.testResource.isCollection() == True
        
 
 
    def testCache(self):
        """
        Assert proper cache management.
        """
        assert self.testResource.getPropertyManager().propertyCache == {}, "At the beginning, the cache must be empty."
        self.testResource.resourceID()
        contained = elements.ResourceID.qname() in self.testResource.getPropertyManager().propertyCache
        assert contained, "After a request, the cache must be non-empty."
        
        for ee in self.testResource.getPropertyManager().cachedProperties:
            contained = ee.qname() in self.testResource.getPropertyManager().propertyCache.keys()
            assert contained, "Property %s must now be in the cache." % `ee`
  
        
    def testInspectResource(self):
        """
        One inspection should exit happily, or raise StopIteration upon termination.
        """
        
        # look at the root, this is most often trivial.
        try:
            client.inspectResource(self.localTestResource)
        except StopIteration, e:
            pass
        assert self.localTestResource.verify()
        
        # look at MISSION ETERNITY
        path = os.sep.join([repositoryPath, "MISSION ETERNITY"])
        af = basic.Basic(path)
        if not os.path.exists(path): 
            return
        
        me = clone.Clone("missioneternity.org")
        assert me.ping(), "missioneternity.org must be reachable for this test."
        
        try:
            client.inspectResource(af)
            assert af.verify(), "resource does not verify after inspection."
        except StopIteration, e:
            pass
        assert True
        
    def testRevision(self):
        revision = self.testResource.revision()
        assert type(revision) == type(0)
        assert revision >= 0
        
    def testOpen(self):
        from angel_app.resource.abstractContentManager import REPR_DIRECTORY
        assert REPR_DIRECTORY == self.testResource.open().read()

        
    def testSignature(self):
        signature = self.testResource.metaDataSignature()
        from angel_app.contrib.ezPyCrypto import key
        k = key()
        k.importKey(self.localTestResource.publicKeyString())
        assert k.verifyString(self.localTestResource.signableMetadata(), signature), "metadata signature validation failed"  
    
