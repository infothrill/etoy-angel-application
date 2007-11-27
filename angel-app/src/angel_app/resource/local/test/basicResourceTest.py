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
from angel_app.resource.remote.clone import Clone
from angel_app.resource.local.test.localResourceTest import LocalResourceTest
from twisted.web2.dav.element import rfc2518
import os
import shutil
import unittest
import zope.interface.verify

AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

class BasicResourceTest(LocalResourceTest):
        
    def testExists(self):
        """
        @return: a C{True} if this resource is accessible, C{False} otherwise.
        """
        assert self.testDirectory.exists()

    def testIsWritable(self):
        assert self.testDirectory.isWritableFile()
        assert Basic(repositoryPath).isWritableFile()

    def testReadFile(self):
        assert self.testText == Basic(self.testFilePath).open().read()  
        
    def testSetProperty(self):
        dp = self.testDirectory.getPropertyManager()
        
        testText = "foo"
        ee = elements.ResourceID.fromString(testText)
        dp.set(ee)
        assert self.testDirectory.resourceID() == testText
    
    def testLocation(self):
        """
        @return the resource's path relative to the site root.
        """
        assert self.testDirectory.relativePath() == "/TEST/"
        
    def testOpen(self):
        from angel_app.resource.abstractContentManager import REPR_DIRECTORY
        assert REPR_DIRECTORY == self.testDirectory.open().read()
    
    def testIsCollection(self):
        """
        Checks whether this resource is a collection resource / directory.
        @return: a C{True} if this resource is a collection resource, C{False}
            otherwise.
        """
        assert self.testDirectory.isCollection()

    def testResourceID(self):
        """
        @return: the id of the resource as C{String}.
        """
        assert type(self.testDirectory.resourceID().toxml()) == type("")
        
    def testRevision(self):
        """
        @return: a C{int} corresponding to the revision number of this resource
        """
        revisionNumber = self.testDirectory.revision()
        assert type(revisionNumber) == type(0)
        assert revisionNumber >= 0

    def testPublicKey(self):
        """
        Make sure the stored public key is a valid ezPyCrypto key.
        """
        from angel_app.contrib.ezPyCrypto import key
        publicKeyString = self.testDirectory.publicKeyString()
        k = key()
        k.importKey(publicKeyString)
        
    def testPath(self):
        "The test resource is a directory, hence the relative URL"
        import urllib
        url = self.testDirectory.relativeURL()
        path = self.testDirectory.relativePath()
        if self.testDirectory.isCollection():
            assert url[-1] == "/"
            assert path[-1] == os.sep
        assert urllib.url2pathname(url) == path

    def testIsRoot(self):
        assert False == self.testDirectory.isRepositoryRoot()

    def testFindChildren(self):
        """
        @return: an iterable over C{uri}.
        """
        assert self.testDirectory.childLinks().qname() == Children.qname()
    
    def testChildren(self):
        assert type(self.testDirectory) == type(self.testDirectory.children()[0])
    
    def testStream(self):
        """
        @return: an object that minimally supports the read() method, which in turn returns the stream contents as a string.
        """
        assert self.testDirectory.open().read() == REPR_DIRECTORY
        
        
    def testClones(self):
        """
        Since the dirResource was freshly created, its clones must all be inherited from the parent.
        """
        clones = self.testDirectory.clones()
        parentClones = self.testDirectory.parent().clones()
        assert len(clones) == len(parentClones)
        
    def testDefaultProperties(self):
        """
        All default property initializers must return WebDAVElement instances which
        are of the same type as the element requested.
        """
        from angel_app.resource.local.propertyManager import defaultMetaData
        dp = self.testDirectory.deadProperties()
        for element in defaultMetaData.keys():
            dme = defaultMetaData[element]
            assert element == dme(dp).qname()
        
        
    def testPropertyIO(self):
        """
        Set a property, read it back out and compare it with the original.
        """
        testProperty = rfc2518.Collection()
        self.testDirectory.deadProperties().set(testProperty)
        assert testProperty.qname() in self.testDirectory.deadProperties().list()
        outProperty = self.testDirectory.deadProperties().get(testProperty.qname())
        assert testProperty.toxml() == outProperty.toxml()
        
    def testInterfaceCompliance(self):
        """
        Verify interface compliance.
        """
        assert IAngelResource.implementedBy(self.testDirectory.__class__)
        assert zope.interface.verify.verifyClass(IAngelResource, self.testDirectory.__class__) 