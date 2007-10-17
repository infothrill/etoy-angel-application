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

from angel_app.config import config
from angel_app.contrib import uuid
from os import sep
from urllib import quote, unquote
from urlparse import urlsplit


# get config:
AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")

def urlPathFromPath(path):
    """
    URL-quote a file system path
    """
    return sep.join(
                       map(
                           quote, 
                           path.split(sep)))
    
def pathFromAbsoluteURI(uri):
    """
    Unquote an absolute URL to afford a file system path
    """    
    (dummyscheme, dummyhost, path, dummyquery, dummyfragment) = urlsplit(uri)
    segments = path.split("/")
    assert segments[0] == "", "URL path didn't begin with '/': %s" % (path,)
    segments = map(unquote, segments[1:])
    return sep.join(segments)


def getHashObject(data = None):
    """
    Returns an object that can create SHA-1 hash values when feeded with data
    using the update() method.
    Optional paramater data is passed to the constructor of the hash object,
    and can be used for more condensed code.
    This method exists solely for python version compatibility.
    """
    # TODO: on python 2.5, remove sha module and use hashlib only
    from platform import python_version_tuple
    (major, minor, dummypatchlevel) = python_version_tuple()
    major = int(major)
    minor = int(minor)
    if (major >=2 and minor < 5 ):
        import sha
        if data:
            obj = sha.new(data)
        else:
            obj = sha.new()            
    else: # python 2.5 + only
        import hashlib
        obj = hashlib.sha1()
        if data:
            obj = hashlib.sha1(data)
        else:
            obj = hashlib.sha1()            
    return obj



def uuidFromPublicKeyString(publicKey):    
    return uuid.UUID( getHashObject(publicKey).hexdigest()[:32] )