import os
from angel_app.log import getLogger
from twisted.web2 import stream
from twisted.web2.dav.element import rfc2518
from angel_app import elements
from angel_app.resource.local.internal.methods import copy, delete, lock, mkcol, move, put
from angel_app.resource.local.basic import Basic
from angel_app.contrib.ezPyCrypto import key as ezKey
from angel_app.config import internal as config
from angel_app.resource.remote.client import inspectResource

import urllib

DEBUG = False

log = getLogger("local.internal")
# DO NOT EXPOSE THIS KEY!!!!
from angel_app.config.internal import loadKeysFromFile

class Crypto(
             lock.Lockable,
             copy.copyMixin,
             delete.Deletable, 
             mkcol.mkcolMixin,
             move.moveMixin,
             put.Putable, 
             Basic):
    """
    <p>
    </p>
    <p>
    See subclasses and angel_app.angelMixins for the implementation of
    specific WebDAV methods.
    </p>
    """
    
    secretKey = loadKeysFromFile()
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        Basic.__init__(self, path, defaultType, indexNames)
        self.fp.exists() and self._initProperties()

    def _initProperties(self):
        """
        Set all required properties to a syntactically meaningful default value, if not already set.
        """
        dp = self.deadProperties()
        for element in elements.requiredKeys:
            if not dp.contains(element.qname()):
                if element in config.defaultMetaData.keys():
                    ee = element(config.defaultMetaData[element](self))
                else:  
                    ee = element()  
                
                DEBUG and log.debug("initializing " + element.sname() + " of " + self.fp.path + " to " + ee.toxml())
                dp.set(ee)
                    
        
    def _inheritClones(self):
        self.deadProperties().set(
                                  self.parent().deadProperties().get(
                                                                     elements.Clones.qname()))
          
    def _updateMetadata(self): 

        self._initProperties()
        #self._inheritClones()        
        # now encrypt and sign, update the containing collection
        self.update(1)

    
    
    def encrypt(self):
        """
        <p>
        Replace the contents of the file with the encrypted data,
        return right away if the resource is a directory or self.secretKey
        is None.
        </p>

        TODO: this uses in-memory encryption, revamp to streams
        """
        
        if self.fp.isdir() or self.secretKey == None: return

        DEBUG and log.debug("encrypting file: " + self.fp.path)
        myFile = self.fp.open() 
        plainText = myFile.read()
        myFile.close()
        cypherText = self.secretKey.encString(plainText)
        DEBUG and log.debug(cypherText)  

        import angel_app.singlefiletransaction
        t = SingleFileTransaction()
        safe = t.open(self.fp, 'wb')
        safe.write(cypherText)
        safe.close()
        t.commit()


    def sign(self):
        """
        Create a cryptographic checksum of the file contents and store
        the public key and checksum in the metadata.

        IMPORTANT: signing of files and directories differs by design:
        directories always have the same signature, because each node
        in the tree can be referenced by another one (Unix mount analogy).
        Therefore, it is not possible to use a directory's name as the 
        value to be signed.
        """
        from angel_app.resource.local.util import getHexDigestForFile

        DEBUG and log.debug("signing file: " + self.fp.path)

        signature = getHexDigestForFile(self.fp)
        self.deadProperties().set(
                                  elements.ContentSignature.fromString(signature)
                                  )
        self.deadProperties().set(
                                  elements.PublicKeyString.fromString(self.secretKey.exportKey())
                                  )
        return signature


    def bumpRevisionNumber(self):
        """
        Increase the revision number by one, if it not initialized, set it to 1.
        """
        nn = self.revisionNumber() + 1
        DEBUG and log.debug("revision number for " + self.fp.path +" now at: " + `nn`)
        self.deadProperties().set(elements.Revision.fromString(`nn`))
        return int(nn)

    def isWritableFile(self):
        """
        A file is writable, if we're the owner of that file, i.e. if
        the signing key associated with the file is our local public key.
        
        Alternatively, if the file does not exist yet, it's considered writable if 
        the parent directory exists and is writable.
        
        @returns True if the location is writable, False otherwise
        """
        
        DEBUG and log.debug("testing for writability of: " + self.fp.path)
        
        if not self.secretKey:
            # we don't even have a private key
            DEBUG and log.debug("Crypto: no key available")
            return False

        
        if not self.fp.exists():
            # the corresponding file does not exist
            
            if not self.parent():
                # this is the root, the root directory _must_ exist, so fail
                return False
            
            if not self.parent().exists():
                DEBUG and log.debug("this is not the root, but the parent directory does not exist")
                return False
            else:
                return self.parent().isWritableFile()
                
                
        myKeyString = self.secretKey.exportKey()    
        fileKeyString = self.getOrSet(elements.PublicKeyString, myKeyString)
        DEBUG and log.debug("public key for " + self.fp.path + ": " + fileKeyString)
        return fileKeyString == myKeyString


    def seal(self):
        """
        Sign the meta data and append the signature to
        the meta data.
        
        @param key: an ezPyCrypto key object.
        
        See also: L{ezPyCrypto.key}
        """
        
        DEBUG and log.debug("Crypto: sealing " + self.fp.path)
        DEBUG and log.debug("Crypto: signable data: " + self.signableMetadata())
        signature = self.secretKey.signString(self.signableMetadata())
        self.deadProperties().set(elements.MetaDataSignature.fromString(signature))
        #storedsignature = self.getOrSet(elements.MetaDataSignature, "0")
        #log.error(signature)
        #log.error(storedsignature)
        DEBUG and log.debug("Crypto: signature is " + signature)
        return signature
    
    def updateParent(self, recursionLimit = 0):
        pp = self.parent()
        log.error(pp.fp.path)
        pp and pp.update()

    def _deRegisterWithParent(self):

        DEBUG and log.debug("entering _deRegisterWithParent for: " + self.fp.path)

        pp = self.parent()
        
        if None == pp:
            log.msg("Can not deregister root resource with parent.")
               
        DEBUG and log.debug(`self.parent()`)
        pdp = pp.deadProperties()
        
        oc = pdp.get(elements.Children.qname()).children
        
        DEBUG and log.debug("resourceName: " + self.resourceName())     
        nc = [cc for cc in oc if not str(cc.childOfType(rfc2518.HRef)) == urllib.quote(self.resourceName())]
        
        pdp.set(elements.Children(*nc))
        pp.seal()
        DEBUG and log.debug("exiting _deRegisterWithParent")
    
    def _registerWithParent(self):

        DEBUG and log.debug("entering _registerWithParent for " + self.fp.path)

        self._initProperties()

        pp = self.parent()
        
        if None == pp:
            log.msg("Can not register root resource with parent.")
        
        pdp = pp.deadProperties()
        
        oc = pdp.get(elements.Children.qname()).children
           
        for cc in oc:
            if str(cc.childOfType(rfc2518.HRef)) == urllib.quote(self.resourceName()):
                DEBUG and log.debug(self.fp.path + ": this resource is already registered with the parent")
                return

        ic = elements.Child(*[
                         rfc2518.HRef(urllib.quote(self.resourceName())),
                         elements.UUID(str(self.parent().keyUUID())),
                         self.resourceID()
                         ])
        
        nc = [cc for cc in oc] + [ic]
        ce = elements.Children(*nc)
        pdp.set(ce)  
        pp.seal()          
        DEBUG and log.debug("exiting _registerWithParent")
    
        
        
    def _changeRegister(self, request):
        """
        @return a callback that deregisters the current resource and registers the request destination resource.
        """       
        
        from angel_app.resource.local.util import resourceFromURI
        
        def ccCallBack(response):
            self._deRegisterWithParent()
            
            destination_uri = request.headers.getHeader("destination")
            DEBUG and log.debug("changeRegister: " + `self.__class__`)
            destination = resourceFromURI(destination_uri, self.__class__)
            destination._registerWithParent()
        
            return response
        
        return ccCallBack

    
    def update(self, recursionLimit = 0):
        
        DEBUG and log.debug("called update on: " + self.fp.path)
        
        if not self.isWritableFile(): 
            raise "not authorized to perform update of signed meta data"

        DEBUG and log.debug("encrypting " + self.fp.path + "?")
        if self.isEncrypted():
            DEBUG and log.debug("encrypting " + self.fp.path)
            self.encrypt()
        DEBUG and log.debug("signing " + self.fp.path)
        self.sign()
        DEBUG and log.debug("bumping revision number for " + self.fp.path)
        self.bumpRevisionNumber()

        
        DEBUG and log.debug("sealing " + self.fp.path)
        self.seal()

        DEBUG and log.debug("Verifying " + self.fp.path)
        DEBUG and self.verify()
        
        # certainly not going to hurt if we do this:
        self.fp.restat()
        
        log.error(self.fp.path + " now at revision: " + self.getOrSet(elements.Revision)) 
        if recursionLimit > 0:
            self.updateParent(recursionLimit - 1)
    
        
    def getResponseStream(self):
        """
        @see Basic.getResponseStream
        """
        DEBUG and log.debug("rendering file in plaintext: " + self.fp.path)
        if self.isEncrypted():
            
            fileContents = self.secretKey.decString(self.fp.open().read())
            return stream.MemoryStream(fileContents, 0, len(fileContents))
        else:
            return Basic.getResponseStream(self)

