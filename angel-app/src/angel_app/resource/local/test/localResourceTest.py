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
from angel_app.elements import Children
from angel_app.resource.IResource import IAngelResource
from angel_app.resource.local.basic import Basic
from angel_app.resource.local.internal.resource import Crypto
from twisted.web2.dav.element import rfc2518
import angel_app.resource.local.basic as bb
import os
import unittest
import zope.interface.verify


AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

class BasicResourceTest(unittest.TestCase):
    
    testDirPath = os.path.sep.join([repositoryPath, "TEST"])

    def setUp(self):
        try:
            os.mkdir(self.testDirPath)
        except OSError, e:
            print `e`

        self.dirResource = Crypto(self.testDirPath) 
        self.dirResource._registerWithParent()
        self.dirResource._updateMetadata()
        
    def tearDown(self):
        self.dirResource._deRegisterWithParent()
        try:
            os.rmdir(self.testDirPath)
        except OSError, e:
            print "not a directory" + `e`
            os.remove(self.testDirPath)
    
        
    def testExists(self):
        """
        @return: a C{True} if this resource is accessible, C{False} otherwise.
        """
        assert self.dirResource.exists()
    
    def testLocation(self):
        """
        @return the resource's path relative to the site root.
        """
        assert self.dirResource.relativePath() == "/TEST/"
    
    def testIsCollection(self):
        """
        Checks whether this resource is a collection resource / directory.
        @return: a C{True} if this resource is a collection resource, C{False}
            otherwise.
        """
        assert self.dirResource.isCollection()

    def testResourceID(self):
        """
        @return: the id of the resource as C{String}.
        """
        assert type(self.dirResource.resourceID().toxml()) == type("")
        
    def testRevision(self):
        """
        @return: a C{int} corresponding to the revision number of this resource
        """
        revisionNumber = self.dirResource.revision()
        assert type(revisionNumber) == type(0)
        assert revisionNumber >= 0

    def testPublicKey(self):
        """
        Make sure the stored public key is a valid ezPyCrypto key.
        """
        from angel_app.contrib.ezPyCrypto import key
        publicKeyString = self.dirResource.publicKeyString()
        k = key()
        k.importKey(publicKeyString)
        
    def testPath(self):
        "The test resource is a directory, hence the relative URL"
        import urllib
        url = self.dirResource.relativeURL()
        path = self.dirResource.relativePath()
        if self.dirResource.isCollection():
            assert url[-1] == "/"
            assert path[-1] == os.sep
        assert urllib.url2pathname(url) == path

    def testFindChildren(self):
        """
        @return: an iterable over C{uri}.
        """
        assert self.dirResource.childLinks().qname() == Children.qname()
    
    def testStream(self):
        """
        @return: an object that minimally supports the read() method, which in turn returns the stream contents as a string.
        """
        assert self.dirResource.open().read() == bb.REPR_DIRECTORY
        
        
    def testClones(self):
        """
        Since the dirResource was freshly created, it's clones must all be inherited from the parent.
        """
        clones = self.dirResource.clones()
        parentClones = self.dirResource.parent().clones()
        assert len(clones) == len(parentClones)
        
    def testDefaultProperties(self):
        """
        All default property initializers must return WebDAVElement instances which
        are of the same type as the element requested.
        """
        from angel_app.resource.local.propertyManager import defaultMetaData
        dp = self.dirResource.deadProperties()
        for element in defaultMetaData.keys():
            dme = defaultMetaData[element]
            assert element == dme(dp).qname()
        
        
    def testPropertyIO(self):
        """
        Set a property, read it back out and compare it with the original.
        """
        testProperty = rfc2518.Collection()
        self.dirResource.deadProperties().set(testProperty)
        assert testProperty.qname() in self.dirResource.deadProperties().list()
        outProperty = self.dirResource.deadProperties().get(testProperty.qname())
        assert testProperty.toxml() == outProperty.toxml()
        
    def testInterfaceCompliance(self):
        """
        Verify interface compliance.
        """
        assert IAngelResource.implementedBy(Basic)
        assert zope.interface.verify.verifyClass(IAngelResource, Basic)
        
    def testInterfaceCompliance(self):
        """
        Verify interface compliance.
        """
        from angel_app.resource.IReadonlyPropertyManager import IReadonlyPropertyManager
        from angel_app.resource.local.propertyManager import PropertyManager
        assert IReadonlyPropertyManager.implementedBy(PropertyManager)
        assert zope.interface.verify.verifyClass(IReadonlyPropertyManager, PropertyManager)  