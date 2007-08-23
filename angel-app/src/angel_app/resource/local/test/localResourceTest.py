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

import os
import unittest
from angel_app.resource.local.internal.resource import Crypto
import angel_app.resource.local.basic as bb

from angel_app.config import config
AngelConfig = config.getConfig()
repositoryPath = AngelConfig.get("common","repository")

class BasicResourceTest(unittest.TestCase):
    
    testDirPath = os.path.sep.join([repositoryPath, "TEST"])

    def setUp(self):
        os.mkdir(self.testDirPath)
        self.dirResource = Crypto(self.testDirPath) 
        self.dirResource._registerWithParent()  
        self.dirResource._updateMetadata()
        
    def tearDown(self):
        self.dirResource._deRegisterWithParent()  
        os.rmdir(self.testDirPath)

    def testWriteNewFile(self):
        raise "not implemented"
    
        
    def testExists(self):
        """
        @return: a C{True} if this resource is accessible, C{False} otherwise.
        """
        assert self.dirResource.exists()
    
    def testLocation(self):
        """
        @return the resource's path relative to the site root.
        """
        assert self.dirResource.relativePath() == "/TEST"
    
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
        revisionNumber = self.dirResource.revisionNumber()
        assert type(revisionNumber) == type(0)
        assert revisionNumber >= 0

    def testFindChildren(self):
        """
        @return: an iterable over C{uri}.
        """
        raise "not implemented"
    
    def testStream(self):
        """
        @return: an object that minimally supports the read() method, which in turn returns the stream contents as a string.
        """
        stream = self.dirResource.getResponseStream()
        assert self.dirResource.getResponseStream().read() == bb.REPR_DIRECTORY

    def testGetProperty(self):
        """
        Reads the given property on this resource.
        @param property: an empty L{davxml.WebDAVElement} class or instance, or
            a qname tuple.
        @return: a L{davxml.WebDAVElement} instance
            containing the value of the given property.
        """
        raise "not implemented"

    def testWriteProperties(self):
        """
        Writes the given property on this resource.
        @param properties a the list of elements.requiredKeys
        """
        raise "not implemented"

    def testListProperties(self):
        """
        @param request: the request being processed.
        @return: a deferred iterable of qnames for all properties defined for
            this resource.
        """
        raise "not implemented"