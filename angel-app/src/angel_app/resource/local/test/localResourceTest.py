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
from angel_app.elements import Children
from angel_app.resource.IResource import IAngelResource
from angel_app.resource.abstractContentManager import REPR_DIRECTORY
from angel_app.resource.local.basic import Basic
from angel_app.resource.local.internal.resource import Crypto
from angel_app.resource.test import resourceTest 
from twisted.web2.dav.element import rfc2518
import os
import shutil
import unittest
import zope.interface.verify

AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

class BasicResourceTest(resourceTest.ResourceTest):
    
    testDirPath = os.path.sep.join([repositoryPath, "TEST"])
    testFilePath = os.path.sep.join([testDirPath, "file.txt"])
    testText = "lorem ipsum"

    def setUp(self):
        try:
            os.mkdir(self.testDirPath)
        except OSError, e:
            print `e`

        cc = Crypto(self.testDirPath) 
        cc._registerWithParent()
        cc._updateMetadata()
        self.testResource = Basic(self.testDirPath)
        open(self.testFilePath, 'w').write(self.testText)
        
        
    def tearDown(self):
        Crypto(self.testDirPath).remove() 
        
    def testExists(self):
        """
        @return: a C{True} if this resource is accessible, C{False} otherwise.
        """
        assert self.testResource.exists()

    def testIsWritable(self):
        assert self.testResource.isWritableFile()
        assert Basic(repositoryPath).isWritableFile()

    def testReadFile(self):
        assert self.testText == Basic(self.testFilePath).open().read()  
        
    def testSetProperty(self):
        dp = self.testResource.getPropertyManager()
        
        testText = "foo"
        ee = elements.ResourceID.fromString(testText)
        dp.set(ee)
        assert self.testResource.resourceID() == testText
    
    def testLocation(self):
        """
        @return the resource's path relative to the site root.
        """
        assert self.testResource.relativePath() == "/TEST/"
        
    def testOpen(self):
        from angel_app.resource.abstractContentManager import REPR_DIRECTORY
        assert REPR_DIRECTORY == self.testResource.open().read()
    
    def testIsCollection(self):
        """
        Checks whether this resource is a collection resource / directory.
        @return: a C{True} if this resource is a collection resource, C{False}
            otherwise.
        """
        assert self.testResource.isCollection()

    def testResourceID(self):
        """
        @return: the id of the resource as C{String}.
        """
        assert type(self.testResource.resourceID().toxml()) == type("")
        
    def testRevision(self):
        """
        @return: a C{int} corresponding to the revision number of this resource
        """
        revisionNumber = self.testResource.revision()
        assert type(revisionNumber) == type(0)
        assert revisionNumber >= 0

    def testPublicKey(self):
        """
        Make sure the stored public key is a valid ezPyCrypto key.
        """
        from angel_app.contrib.ezPyCrypto import key
        publicKeyString = self.testResource.publicKeyString()
        k = key()
        k.importKey(publicKeyString)
        
    def testPath(self):
        "The test resource is a directory, hence the relative URL"
        import urllib
        url = self.testResource.relativeURL()
        path = self.testResource.relativePath()
        if self.testResource.isCollection():
            assert url[-1] == "/"
            assert path[-1] == os.sep
        assert urllib.url2pathname(url) == path

    def testIsRoot(self):
        assert False == self.testResource.isRepositoryRoot()

    def testFindChildren(self):
        """
        @return: an iterable over C{uri}.
        """
        assert self.testResource.childLinks().qname() == Children.qname()
    
    def testStream(self):
        """
        @return: an object that minimally supports the read() method, which in turn returns the stream contents as a string.
        """
        assert self.testResource.open().read() == REPR_DIRECTORY
        
        
    def testClones(self):
        """
        Since the dirResource was freshly created, its clones must all be inherited from the parent.
        """
        clones = self.testResource.clones()
        parentClones = self.testResource.parent().clones()
        assert len(clones) == len(parentClones)
        
    def testDefaultProperties(self):
        """
        All default property initializers must return WebDAVElement instances which
        are of the same type as the element requested.
        """
        from angel_app.resource.local.propertyManager import defaultMetaData
        dp = self.testResource.deadProperties()
        for element in defaultMetaData.keys():
            dme = defaultMetaData[element]
            assert element == dme(dp).qname()
        
        
    def testPropertyIO(self):
        """
        Set a property, read it back out and compare it with the original.
        """
        testProperty = rfc2518.Collection()
        self.testResource.deadProperties().set(testProperty)
        assert testProperty.qname() in self.testResource.deadProperties().list()
        outProperty = self.testResource.deadProperties().get(testProperty.qname())
        assert testProperty.toxml() == outProperty.toxml()
        
    def testInterfaceCompliance(self):
        """
        Verify interface compliance.
        """
        assert IAngelResource.implementedBy(self.testResource.__class__)
        assert zope.interface.verify.verifyClass(IAngelResource, self.testResource.__class__) 