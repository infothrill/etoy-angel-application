"""
Definition of AngelFile metadata (xattr) XML elements. 
"""

legalMatters = """
 Copyright (c) 2005, etoy.VENTURE ASSOCIATION
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
    weird but true). hmm. maybe move this into a reference in the parent directory.
    """
    name = "deleted"     

class Encrypted (WebDAVTextElement):
    """
    Whether the file contents are encrypted.
    """
    name = "encrypted"   


class Child (WebDAVElement):
    """
    Specifies a child of an angel-file (as a local, relative, url).
    TODO: add support for child keys specifying owners
    """
    name = "child"

    allowed_children = {
        (dav_namespace, "href"): (1, 1),
        }

class Children (WebDAVElement):
    """
    List of zero or more clones of a specific angel-file.
    """
    name = "children"
    
    allowed_children = {
        (dav_namespace, "child"): (0, None),
        }



# the above keys must be signed in order for the 
# AngelFile to be valid, i.e. the keys that are signed in the Crypto.seal() operation

signedKeys = [Revision, ContentSignature, PublicKeyString, Deleted, Encrypted,  Children]

class MetaDataSignature (WebDAVTextElement):
    """
    Signature of the metadata tags that need to be signed.
    """
    name = "metaDataSignature"     

class UUID (WebDAVTextElement):
    """
    A universally unique ID as defined in RFC 4122.
    """
    name = "uuid"

class CloneSig (WebDAVTextElement):
    """
    The clone sig is an xml representation of the union of the signed keys
    and the metadata signature. A clone sig therefore encapsulates all the
    meta data (veryfiable via the metaDataSignature) that's necessary to
    identify and validate a clone. 
    """
    name = "cloneSig"
    
    # require the presence of exactly one element of each signed key and the meta
    # data signature
    allowed_children = dict([
                             (
                             (dav_namespace, element.name), 
                             (1, 1)
                             ) 
                            for element in 
                            signedKeys + [MetaDataSignature]
                            ])

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


# the above keys are _required_ for the angel-app to be (even conceptually)
# operational. It is convenient to provide additional information for performance
# and scalability.

# the keys that are used in the self.seal() operation of Crypto files
# TODO: clean up
requiredKeys = signedKeys + [MetaDataSignature]
# the keys that are used in the maintainer loop
interestingKeys = requiredKeys + [Clones]


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
