"""
Definition of AngelFile metadata (xattr) XML elements. 
"""

legalMatters = """
 Copyright (c) 2005, etoy.CORPORATION
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

from twisted.web2.dav.element.base import WebDAVElement, WebDAVTextElement, dav_namespace

class Revision (WebDAVTextElement):
    """
    The revision number of an AngelFile.
    """
    name = "revision"

class ContentSignature (WebDAVTextElement):
    """
    The cryptographic signature of the contents of the AngelFile.
    """
    name = "contentSignature"
    
class PublicKeyString (WebDAVTextElement):
    """
    String representation of the public key of the cryptographic key pair that authorizes for
    writing to the file.
    """
    name = "publicKeyString" 
    
class Deleted (WebDAVTextElement):
    """
    Whether the file has been deleted (in which case the metadata must still be available!
    weird but true).
    """
    name = "deleted"     

# the above keys must be signed in order for the 
# AngelFile to be valid

signedKeys = [Revision, ContentSignature, PublicKeyString, Deleted]

class MetaDataSignature (WebDAVTextElement):
    """
    Signature of the metadata tags that need to be signed.
    """
    name = "metaDataSignature"     

class Clone (WebDAVElement):
    """
    Specifies a clone of an angel-file (as a url)
    """
    name = "clone"

    allowed_children = {
        (dav_namespace, "href"): (1, 1),
        }

class Clones (WebDAVElement):
    """
    List of zero or more clones of a specific angel-file.
    """
    name = "clones"
    
    allowed_children = {
        (dav_namespace, "clone"): (0, None),
        }
    
class Children (WebDAVTextElement):
    """
    The children (and all their clones) of an angel-file which is a collection.
    """
    name = "children"
    
    allowed_children = {
        (dav_namespace, "clones"): (0, None),
        }


# the above keys are _required_ for the angel-app to be (even conceptually)
# operational. It is convenient to provide additional information for performance
# and scalability.
requiredKeys = signedKeys + [MetaDataSignature, Clones, Children]

class ForceLocalCache (WebDAVTextElement):
    """
    If this tag evaluates to true, (e.g. its integer value is non-zero),
    a local clone of this file is always maintained. This is always the case
    for now.
    """
    name = "forceLocalCache" 
    
class ForceEncryption (WebDAVTextElement):
    """
    If this tag evaluates to false, (e.g. its integer value is non-zero),
    the contents of this file are stored in plaintext. This is always false
    for now.
    """
    name = "encrypted" 