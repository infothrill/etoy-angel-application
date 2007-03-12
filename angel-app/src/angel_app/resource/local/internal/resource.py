import os
from angel_app.log import getLogger
from twisted.web2 import stream
from twisted.web2.dav.element import rfc2518
from angel_app import elements
from angel_app.resource.local.internal.methods import copy, delete, lock, mkcol, move, put
from angel_app.resource.local.basic import Basic
from angel_app.contrib.ezPyCrypto import key as ezKey
from angel_app.resource.remote.client import inspectResource
from angel_app.resource.local import util
from angel_app import elements

import urllib

log = getLogger(__name__)
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
    WebDAV resource interface for presenter.
    """
    
    keyRing = loadKeysFromFile()
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        
        Basic.__init__(self, path, defaultType, indexNames)
         
        self.defaultValues[elements.ResourceID] = lambda x : util.makeResourceID(x.relativePath())
                    
    def secretKey(self):
        
        pks = None
        if self.exists():                
            pks = self.publicKeyString()
        elif self.parent().exists():
            pks = self.parent().publicKeyString()
        
        if pks == None:
            raise "Unable to look up public key for resource: " + self.fp.path
        
        log.debug("keys on key ring: " + " ".join(Crypto.keyRing.keys()))
        
        if pks not in Crypto.keyRing.keys():
            error = "Unable to look up secret key for public key %s on resource: %s. Found: " \
                % (pks, self.fp.path)
            for key in Crypto.keyRing.keys():
                error += key
            log.warn(error)
            raise error
        
        return Crypto.keyRing[pks]
  
    def _inheritClones(self):
        self.deadProperties().set(
                                  self.parent().deadProperties().get(
                                                                     elements.Clones.qname()))
          
    def _updateMetadata(self): 

        log.debug("entering _updateMetadata for resource " + self.fp.path)
        self.update(1)
        log.debug("exiting _updateMetadata for resource " + self.fp.path)

    
    
    def encrypt(self):
        """
        <p>
        Replace the contents of the file with the encrypted data,
        return right away if the resource is a directory or self.secretKey
        is None.
        </p>

        TODO: this uses in-memory encryption, revamp to streams
        """
        
        if self.fp.isdir() or self.secretKey() == None: return

        log.debug("encrypting file: " + self.fp.path)
        myFile = self.fp.open() 
        plainText = myFile.read()
        myFile.close()
        cypherText = self.secretKey().encString(plainText)
        log.debug(cypherText)  

        import angel_app.singlefiletransaction
        t = angel_app.singlefiletransaction.SingleFileTransaction()
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
        log.debug("signing file: " + self.fp.path)

        signature = self._computeContentHexDigest()
        self.deadProperties().set(
                                  elements.ContentSignature.fromString( signature )
                                  )
        self.deadProperties().set(
                                  elements.PublicKeyString.fromString( self.secretKey().exportKey() )
                                  )
        return signature

    def bumpRevisionNumber(self):
        """
        Increase the revision number by one, if it not initialized, set it to 1.
        """
        nn = self.revisionNumber() + 1
        log.debug("revision number for " + self.fp.path +" now at: " + `nn`)
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
        
        log.debug("testing for writability of: " + self.fp.path)
        
        try: 
            self.secretKey()
        except:
            # we don't even have a private key
            log.debug("Crypto: no key available for resource: " + self.fp.path)
            return False

        
        if not self.fp.exists():
            # the corresponding file does not exist
            
            if not self.parent():
                # this is the root, the root directory _must_ exist, so fail
                return False
            
            if not self.parent().exists():
                log.debug("this is not the root, but the parent directory does not exist")
                return False
            else:
                return self.parent().isWritableFile()
                
                
        myKeyString = self.secretKey().exportKey()    
        fileKeyString = self.publicKeyString()
        log.debug("public key for " + self.fp.path + ": " + fileKeyString)
        return fileKeyString == myKeyString

    def seal(self):
        """
        Sign the meta data and append the signature to
        the meta data.
        
        @param key: an ezPyCrypto key object.
        
        See also: L{ezPyCrypto.key}
        """
        
        log.debug("Crypto: sealing " + self.fp.path)
        signature = self.secretKey().signString(self.signableMetadata())
        self.deadProperties().set(elements.MetaDataSignature.fromString(signature))
        log.debug("Crypto: signature is " + signature)
        return signature
    
    def updateParent(self, recursionLimit = 0):
        pp = self.parent()
        log.debug("updating parent of " + self.fp.path)
        pp and pp.update()

    def _deRegisterWithParent(self):
        """
        Remove this resource from its parent's child elements.
        """
        log.debug("entering _deRegisterWithParent for: " + self.fp.path)

        pp = self.parent()
        
        if None == pp:
            log.warn("Can not deregister root resource with parent.")
               
        log.debug(`self.parent()`)
        pdp = pp.deadProperties()
        
        oc = pdp.get(elements.Children.qname()).children
        
        log.debug("resourceName: " + self.resourceName())     
        nc = [cc for cc in oc if not str(cc.childOfType(rfc2518.HRef)) == self.relativeURL()]
        
        pdp.set(elements.Children(*nc))
        pp.seal()
        log.debug("exiting _deRegisterWithParent")
    
    def _registerWithParent(self):
        """
        Add this resource to its parent's child elements.
        """
        log.debug("entering _registerWithParent for " + self.fp.path)

        if self.isRepositoryRoot():
            log.msg("Can not register root resource with parent.")
        
        pdp = self.parent().deadProperties()
        
        oc = pdp.get(elements.Children.qname()).children
           
        for cc in oc:
            if str(cc.childOfType(rfc2518.HRef)) == urllib.quote(self.resourceName()):
                log.debug(self.fp.path + ": this resource is already registered with the parent")
                return

        ic = elements.Child(*[
                         rfc2518.HRef(self.relativeURL()),
                         elements.UUID(str(self.keyUUID())),
                         self.resourceID()
                         ])
        
        nc = [cc for cc in oc] + [ic]
        ce = elements.Children(*nc)
        pdp.set(ce)  
        self.parent().seal()          
        log.debug("exiting _registerWithParent")
    
        
        
    def _changeRegister(self, request):
        """
        @return a callback that deregisters the current resource and registers the request destination resource.
        """       
        
        from angel_app.resource.local.util import resourceFromURI
        
        def ccCallBack(response):
            self._deRegisterWithParent()
            
            destination_uri = request.headers.getHeader("destination")
            log.debug("changeRegister: " + `self.__class__`)
            destination = resourceFromURI(destination_uri, self.__class__)
            destination._registerWithParent()
        
            return response
        
        return ccCallBack

    
    def update(self, recursionLimit = 0):
        
        log.debug("called update on: " + self.fp.path)
        
        if not self.isWritableFile(): 
            raise "not authorized to perform update of signed meta data"

        log.debug("encrypting " + self.fp.path + "?")
        if self.isEncrypted():
            log.debug("encrypting " + self.fp.path)
            self.encrypt()
        log.debug("signing " + self.fp.path)
        self.sign()
        log.debug("bumping revision number for " + self.fp.path)
        self.bumpRevisionNumber()

        
        log.debug("sealing " + self.fp.path)
        self.seal()

        log.debug("Verifying " + self.fp.path)
        # DEBUG and self.verify() # TODO: this should go!
        
        # certainly not going to hurt if we do this:
        self.fp.restat()
        
        log.debug(self.fp.path + " now at revision: " + `self.revisionNumber()`) 
        if recursionLimit > 0:
            self.updateParent(recursionLimit - 1)
            
        log.debug("done update for resource " + self.fp.path)
    
        
    def getResponseStream(self):
        """
        @see Basic.getResponseStream
        """
        log.debug("rendering file in plaintext: " + self.fp.path)
        if self.isEncrypted():
            
            fileContents = self.secretKey().decString(self.fp.open().read())
            return stream.MemoryStream(fileContents, 0, len(fileContents))
        else:
            return Basic.getResponseStream(self)



# TODO move key ring to separate module
def reloadKeys():  
    log.info("reloading keys") 
    Crypto.keyRing = loadKeysFromFile()
    log.info("available keys: " + `Crypto.keyRing.keys()`)
    
reloadKeys()