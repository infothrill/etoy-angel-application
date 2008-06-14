import os
import urllib

from twisted.web2 import stream
from twisted.web2.dav.element import rfc2518

from angel_app import elements
from angel_app.config.internal import loadKeysFromFile
from angel_app.log import getLogger
from angel_app.resource.local.basic import Basic
from angel_app.resource.local.internal.methods import copy, delete, lock, mkcol, move, put

log = getLogger(__name__)
# DO NOT EXPOSE THIS KEY!!!!

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
        self.update(1)

    
    
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


    def _signContent(self):
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
        self.deadProperties().set(elements.Revision.fromString(`nn`))
        return int(nn)

    def isWritableFile(self):
        """
        DEPRECATED. Now included in Basic.
        
        A file is writable, if we're the owner of that file, i.e. if
        the signing key associated with the file is our local public key.
        
        Alternatively, if the file does not exist yet, it's considered writable if 
        the parent directory exists and is writable.
        
        @returns True if the location is writable, False otherwise
        """    
        try: 
            self.secretKey()
        except KeyError, e:
            error = "Crypto: no key available for resource: " + self.fp.path + "\n"
            error += `e`
            # we don't even have a private key
            log.info(error)
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
        return fileKeyString == myKeyString

    def seal(self):
        """
        Sign the meta data and append the signature to
        the meta data.
        
        @param key: an ezPyCrypto key object.
        
        See also: L{ezPyCrypto.key}
        """
        signature = self.secretKey().signString(self.signableMetadata())
        self.deadProperties().set(elements.MetaDataSignature.fromString(signature))
        return signature
    
    def updateParent(self, recursionLimit = 0):
        """
        TODO: This is a one-liner and should go into self.update()
        """
        pp = self.parent()
        pp and pp.update()

    def _deRegisterWithParent(self):
        """
        Remove this resource from its parent's child elements.
        """
        pp = self.parent()
        
        if None == pp:
            log.warn("Can not deregister root resource with parent.")
               
        pdp = pp.deadProperties()
        
        oc = pdp.get(elements.Children.qname()).children
         
        nc = [cc for cc in oc if not str(cc.childOfType(rfc2518.HRef)) == urllib.quote(self.resourceName())]
        
        pdp.set(elements.Children(*nc))
        pp.bumpRevisionNumber()
        pp.seal()
    
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
        
        self.parent().bumpRevisionNumber()
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
            destination = resourceFromURI(destination_uri, self.__class__)
            destination._registerWithParent()
        
            return response
        
        return ccCallBack
        
    def remove(self):

        # security check
        if self.isRepositoryRoot():
            raise Exception("Cowardly refusing to delete the root directory.")
        
        if self.isWritableFile():
            self._deRegisterWithParent()
            # else we don't own this, so can't

        super(Crypto, self).remove()
    
    def update(self, recursionLimit = 0):
        
        if not self.isWritableFile(): 
            raise RuntimeError, "not authorized to perform update of signed meta data"

        if self.isEncrypted():
            self.encrypt()

        self._signContent()

        self.bumpRevisionNumber()

        self.seal()
        
        # certainly not going to hurt if we do this:
        self.fp.restat()
        
        if recursionLimit > 0:
            self.updateParent(recursionLimit - 1)
    
        
    def getResponseStream(self):
        """
        Stream the file contents (after decryption, if necessary).
        
        @see Basic.getResponseStream
        """
        if self.isEncrypted():
            
            fileContents = self.secretKey().decString(self.fp.open().read())
            return stream.MemoryStream(fileContents, 0, len(fileContents))
        else:
            return Basic.getResponseStream(self)



# TODO move key ring to separate module
def reloadKeys():  
    log.info("reloading keys") 
    Crypto.keyRing = loadKeysFromFile()
    
reloadKeys()