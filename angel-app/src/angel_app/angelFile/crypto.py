from twisted.python import log
from twisted.web2 import stream
from angel_app import elements
from angel_app.angelMixins import delete, put
from angel_app.angelFile.basic import Basic
from ezPyCrypto import key as ezKey

DEBUG = False

# DO NOT EXPOSE THIS KEY!!!!
from angel_app.crypto import loadKeysFromFile

class Crypto(delete.Deletable, put.Putable, Basic):
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

    def signableMetadata(self):
        """
        Returns a string representation of the metadata that needs to
        be signed.
        """
        pp = self.deadProperties()
        return "".join([
                                  `pp.get(key.qname())`
                                  for key in elements.signedKeys
                                  ])


    def seal(self):
        """
        Sign the meta data and append the signature to
        the meta data.
        
        @param key: an ezPyCrypto key object.
        
        See also: L{ezPyCrypto.key}
        """

        signature = self.secretKey.signString(self.signableMetadata())
        self.deadProperties().set(elements.MetaDataSignature.fromString(signature))
        #storedsignature = self.getOrSet(elements.MetaDataSignature, "0")
        #log.err(signature)
        #log.err(storedsignature)
        return signature

    
    def update(self):
        
        DEBUG and log.err("called update on: " + self.fp.path)
        
        if not self.isWritableFile(): 
            raise "not authorized to perform update of signed meta data"
        
        self.encrypt()
        self.sign()
        self.bumpRevisionNumber()
        self.seal()

        DEBUG and self.verify()
        
        # certainly not going to hurt if we do this:
        self.fp.restat()
        
        log.err(self.fp.path + " now at revision: " + self.getOrSet(elements.Revision)) 
    
    def verify(self):
        
        publicKey = ezKey()
        publicKey.importKey(self.get(elements.PublicKeyString))

        contentSignature = self.get(elements.ContentSignature)
        #DEBUG and log.err("verify(): signature: " + contentSignature)
        dataIsCorrect = publicKey.verifyString(
                                  self.contentAsString(),
                                  contentSignature)
        DEBUG and log.err("data signature for file " + self.fp.path + " is correct: " + `dataIsCorrect`)
            
        metaDataIsCorrect = publicKey.verifyString(
                                  self.signableMetadata(),
                                  self.getOrSet(elements.MetaDataSignature))
        
        DEBUG and log.err("meta data signature for file " + self.fp.path + " is correct: " + `metaDataIsCorrect`)
            
        return dataIsCorrect and metaDataIsCorrect
    
    
        
    def getResponseStream(self):
        """
        vincent: slurp and decrypt the file, then make a memory 
        stream out of it
        response.stream = stream.FileStream(f, 0, self.fp.getsize())
        TODO: very inefficient and unsafe
        the proper way to proceed would be the following:
        check if the file is encrypted (should be an xattr flag),
        if it is, decrypt, otherwise return the file right away.
        """
        fileContents = self.secretKey.decString(self.fp.open().read())
        return stream.MemoryStream(fileContents, 0, len(fileContents))