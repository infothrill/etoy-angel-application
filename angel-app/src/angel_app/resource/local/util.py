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

author = """Vincent Kraeutler, 2006"""

from urllib import quote, unquote
from urlparse import urlsplit
from os import sep
from angel_app.contrib import uuid
import time

# get config:
from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")

def resourceFromURI(uri, resourceClass):
    
    (scheme, host, path, query, fragment) = urlsplit(uri)
    segments = path.split("/")
    assert segments[0] == "", "URL path didn't begin with '/': %s" % (path,)
    segments = map(unquote, segments[1:])
    path = repository + sep + sep.join(segments)
    return resourceClass(path)

def getHashObject(data = None):
    """
    Returns an object that can create SHA-1 hash values when feeded with data
    using the update() method.
    Optional paramater data is passed to the constructor of the hash object,
    and can be used for more condensed code.
    This method exists solely for python version compatibility.
    """
    from platform import python_version_tuple
    (major,minor,patchlevel) = python_version_tuple()
    major = int(major)
    minor = int(minor)
    if (major >=2 and minor < 5 ):
        import sha
        if data:
            obj = sha.new(data)
        else:
            obj = sha.new()            
    else:
        import hashlib
        obj = hashlib.sha1()
        if data:
            obj = hashlib.sha1(data)
        else:
            obj = hashlib.sha1()            
    return obj

def getHexDigestForFile(fp):
    hash = getHashObject()
    if fp.isdir(): 
        hash.update("directory") # directories always have the same signature
    else:
        myFile = fp.open()
        bufsize = 4096 # 4 kB
        while True:
            buf = myFile.read(bufsize)
            if len(buf) == 0:
                break
            hash.update(buf)
        myFile.close()
    return hash.hexdigest()


class StringReader:
    """
    Class to read from a string in similar fashion to a file object,
    using the method read()
    """
    def __init__(self, value):
        self.value = value
        self._offset = 0
        self._len = len(value)

    def read(self, size = -1):
        if size < 0: # read all until EOF
            size = self._len - self._offset
        elif size == 0:
            return ''
        else: # size > 0
            dataleft = self._len - self._offset
            if dataleft <= 0:  # read all until EOF
                size = self._len - self._offset
        start = self._offset
        end = self._offset + size
        self._offset = end
        return self.value[start:end]

    def close(self):
        self._offset = 0

def testStringReader():
        import sys
        string = "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.\nThis is on a new line.\n"
        str = StringReader(string)
        bufsize = 5
        while True:
            buf = str.read(bufsize)
            if len(buf) == 0:
                break
            else:
                sys.stdout.write(buf)

def uuidFromPublicKeyString(publicKey):    
    return uuid.UUID( getHashObject(publicKey).hexdigest()[:32] )


def getResourceIDFromParentLinks(resource):
    """
    Extracts the resource's ID from the Child links of the parent.
    """
    # otherwise, take the resourceID delivered from the parent
    children = resource.parent().deadProperties().get(elements.Children.qname()).children
        
    # make a list of all linked resource names
    linkedResourceNames = [str(child.childOfType(rfc2518.HRef.qname())) for child in children]
        
    # get the index of the child we're actually interested in
    try:
        linkIndex = linkedResourceNames.index(urllib.pathname2url(resource.resourceName()))
    except ValueError:
        log.error("Could not find resource %s in parent's links." % resource.relativePath())
        # re-raise the exception
        raise
        
    # this is the child we actually want
    child = children[linkIndex]
    log.debug("child for resourceID: " + `child`)
        
    return str(child.childOfType(elements.ResourceID.qname()).children[0])


def makeResourceID(relativePath = ""):
    """
    Generate a new resourceID for a (new) resource.
    """
    return relativePath + `time.gmtime()`

if __name__ == "__main__":
    testStringReader()
