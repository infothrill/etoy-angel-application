import os
from angel_app.log import getLogger
from twisted.web2 import stream
from twisted.web2.dav.element import rfc2518
from angel_app.resource.local.internal.methods import copy, delete, lock, mkcol, move, put
from angel_app.resource.local.basic import Basic
from angel_app import elements

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

    def davComplianceClasses(self):
        """
        Level 2 compliance implies support for LOCK, UNLOCK, which we support on the internal interface.
        """
        return ("1", "2")
                    
    def secretKey(self):
        """
        Return the secret key corresponding to the public key of this resource (or the parent resource,
        if this resource does not actually exist on the file system).
        """
        pks = None
        if self.exists():                
            pks = self.publicKeyString()
        elif self.parent().exists():
            pks = self.parent().publicKeyString()
        
        if pks == None:
            raise KeyError, "Unable to look up public key for resource: " + self.fp.path
        
        if pks not in Crypto.keyRing.keys():
            error = "Unable to look up secret key for public key %s on resource: %s. Found: " \
                % (pks, self.fp.path)
            for key in Crypto.keyRing.keys():
                error += key
            log.warn(error)
            raise KeyError, error
        
        return Crypto.keyRing[pks]
          
    def _updateMetadata(self): 
        """
        Update the metadata for this resource and its parent.
        
        TODO: One wonders why this is a separate method. It's confusing this way.
        On the other hand, just writing self.update(1) would be even more confusing.
        On a similar note: why is this method "protected", when the (only) method it
        calls is public?
        """
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
        """
        
        if self.fp.isdir() or self.secretKey() == None: return

        import angel_app.singlefiletransaction

        log.debug("encrypting file: " + self.fp.path)

        encrypter = self.secretKey()
        myFile = self.fp.open()
        t = angel_app.singlefiletransaction.SingleFileTransaction()
        safe = t.open(self.fp, 'wb')

        EOF = False
        bufsize = 1024 # 1 kB
        encrypter.encStart()
        while not EOF:
            data = myFile.read(bufsize)
            if len(data) > 0:
                encdata = encrypter.encNext(data)
            else:
                encdata = encrypter.encEnd()
                EOF = True
            safe.write(encdata)
        myFile.close()
        safe.close()
        t.commit() # TODO: only commit if encryption worked!


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
        nn = self.revision() + 1
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
        except KeyError, e:
            error = "Crypto: no key available for resource: " + self.fp.path + "\n"
            error += `e`
            # we don't even have a private key
            log.info(error)
            print error
            return False

        
        if not os.path.exists(self.fp.path):
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
        """
        TODO: This is a one-liner and should go into self.update()
        """
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
        nc = [cc for cc in oc if not str(cc.childOfType(rfc2518.HRef)) == self.quotedResourceName()]
        
        pdp.set(elements.Children(*nc))
        pp.seal()
        log.debug("exiting _deRegisterWithParent")
    
    def _registerWithParent(self):
        """
        Add this resource to its parent's child elements.
        """

        if self.isRepositoryRoot():
            raise RuntimeError, "Can not register root resource with parent."
        
        oc = [cc for cc in self.parent().childLinks().children]

        ic = self.getChildElement()

        if ic in oc:
            # this resource is already registered with the parent"
            return

        # append this child element to the parents child elements
        nc = oc + [ic]
        ce = elements.Children(*nc)
        
        # add to parent and seal parent             
        dummypdp = self.parent().deadProperties().set(ce)  
        self.parent().seal()          
    
        
        
    def _changeRegister(self, request):
        """
        Needed for copy and move operations.
        
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
            raise RuntimeError, "not authorized to perform update of signed meta data"

        if self.isEncrypted():
            self.encrypt()

        self.sign()

        self.bumpRevisionNumber()

        self.seal()
        
        # certainly not going to hurt if we do this:
        self.fp.restat()
        
        log.debug(self.fp.path + " now at revision: " + `self.revision()`) 
        if recursionLimit > 0:
            self.updateParent(recursionLimit - 1)
            
        log.debug("done update for resource " + self.fp.path)
    
        
    def getResponseStream(self):
        """
        Stream the file contents (after decryption, if necessary).
        
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