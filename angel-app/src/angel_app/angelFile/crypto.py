from twisted.python import log
from twisted.web2 import stream
from angel_app import elements
from angel_app.davMethods import copy, delete, lock, mkcol, move, put
from angel_app.angelFile.basic import Basic
from ezPyCrypto import key as ezKey

DEBUG = False

# DO NOT EXPOSE THIS KEY!!!!
from angel_app.crypto import loadKeysFromFile

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
    
    
    def encrypt(self):
        """
        <p>
        Replace the contents of the file with the encrypted data,
        return right away if the resource is a directory or self.secretKey
        is None.
        </p>

        TODO: this implementation is dog slow and non-atomic. Revamp.
        """
        
        if self.fp.isdir() or self.secretKey == None: return
        
        myFile = self.fp.open() 
        plainText = myFile.read()
        myFile.close()
        cypherText = self.secretKey.encString(plainText)
        DEBUG and log.err("encrypting file: " + self.fp.path)
        myFile = self.fp.open("w") 
        myFile.write(cypherText)
        myFile.flush()
        myFile.close()
        DEBUG and log.err(cypherText)  

    def sign(self):
        """
        Sign the file contents and store the public key and signature in the metadata.
        If the secretKey is 
        """
        
        DEBUG and log.err("signing file: " + self.fp.path)
        
        # TODO: this sucks, too
        if self.fp.isdir(): 
            signature = self.secretKey.signString("directory")
        else:
            myFile = self.fp.open()
            fileContents = myFile.read()
            myFile.close()
            signature = self.secretKey.signString(fileContents)
        #signedKeys["contentSignature"].data = signature
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
        DEBUG and log.err("revision number for " + self.fp.path +" now at: " + `nn`)
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
        
        DEBUG and log.err("testing for writability of: " + self.fp.path)
        
        if not self.secretKey:
            # we don't even have a private key
            DEBUG and log.err("no key available")
            return False

        
        if not self.fp.exists():
            # the corresponding file does not exist
            if not self.fp.parent().exists():
                # also the parent directory does not exist
                return False
            else:
                # TODO: as soon as we have a running maintenance loop
                # comment out this line
                return True
                # and uncomment this:
                #return AngelFile(self.fp.parent().path).isWritableFile()
                
                
        myKeyString = self.secretKey.exportKey()    
        fileKeyString = self.getOrSet(elements.PublicKeyString, myKeyString)
        DEBUG and log.err("public key for " + self.fp.path + " " + fileKeyString)
        return fileKeyString == myKeyString


    def seal(self):
        """
        Sign the meta data and append the signature to
        the meta data.
        
        @param key: an ezPyCrypto key object.
        
        See also: L{ezPyCrypto.key}
        """

        self.getOrSet(elements.Deleted, "0")
        
        signature = self.secretKey.signString(self.signableMetadata())
        self.deadProperties().set(elements.MetaDataSignature.fromString(signature))
        #storedsignature = self.getOrSet(elements.MetaDataSignature, "0")
        #log.err(signature)
        #log.err(storedsignature)
        return signature
    
    def parent(self):
        """
        TODO: this needs a check to not go beyond the root.
        """
        log.err(self.fp.path.split("/"))
        if self.fp.path.split("/") == ("repository"): 
            # root directory has no parent
            return None 
        return Crypto(self.fp.parent().path)
    
    def updateParent(self, recursionLimit = 0):
        pp = self.parent()
        log.err(pp.fp.path)
        pp and pp.update()
    
    def update(self, recursionLimit = 0):
        
        DEBUG and log.err("called update on: " + self.fp.path)
        
        if not self.isWritableFile(): 
            raise "not authorized to perform update of signed meta data"

        if self.isEncrypted():
            self.encrypt()
        self.sign()
        self.bumpRevisionNumber()
        self.seal()

        DEBUG and self.verify()
        
        # certainly not going to hurt if we do this:
        self.fp.restat()
        
        log.err(self.fp.path + " now at revision: " + self.getOrSet(elements.Revision)) 
        if recursionLimit > 0:
            self.updateParent(recursionLimit - 1)
    
    
        
    def getResponseStream(self):
        """
        @see Basic.getResponseStream
        """
        DEBUG and log.err("rendering file in plaintext: " + self.fp.path)
        if self.isEncrypted():
            
            fileContents = self.secretKey.decString(self.fp.open().read())
            return stream.MemoryStream(fileContents, 0, len(fileContents))
        else:
            return Basic.getResponseStream(self)
