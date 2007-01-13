import os
#from twisted.python import log
from angel_app.log import getLogger
from twisted.web2 import stream
from twisted.web2.dav.element import rfc2518
from angel_app import elements
from angel_app.resource.local.internal.methods import copy, delete, lock, mkcol, move, put
from angel_app.resource.local.basic import Basic
from ezPyCrypto import key as ezKey
from angel_app.config import internal as config

DEBUG = True

log = getLogger()
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
        DEBUG and log.debug("_initProperties for " + self.fp.path)
        dp = self.deadProperties()
        for element in elements.requiredKeys:
            if not dp.contains(element.qname()):
                if element in config.defaultMetaData.keys():
                    ee = element(config.defaultMetaData[element](self))
                else:  
                    ee = element()  
                
                DEBUG and log.debug("initializing " + element.sname() + " of " + self.fp.path + " to " + ee.toxml())
                dp.set(ee)
        DEBUG and log.debug("done _initProperties for: " + self.fp.path)
                    
        
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

        TODO: this implementation is dog slow and non-atomic. Revamp.
        """
        
        if self.fp.isdir() or self.secretKey == None: return
        
        myFile = self.fp.open() 
        plainText = myFile.read()
        myFile.close()
        cypherText = self.secretKey.encString(plainText)
        DEBUG and log.error("encrypting file: " + self.fp.path)
        myFile = self.fp.open("w") 
        myFile.write(cypherText)
        myFile.flush()
        myFile.close()
        DEBUG and log.error(cypherText)  

    def sign(self):
        """
        Sign the file contents and store the public key and signature in the metadata.
        If the secretKey is 
        """
        
        DEBUG and log.error("signing file: " + self.fp.path)
        
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
        DEBUG and log.error("revision number for " + self.fp.path +" now at: " + `nn`)
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
        
        DEBUG and log.error("testing for writability of: " + self.fp.path)
        
        if not self.secretKey:
            # we don't even have a private key
            DEBUG and log.error("Crypto: no key available")
            return False

        
        if not self.fp.exists():
            # the corresponding file does not exist
            
            if not self.parent():
                # this is the root, the root directory _must_ exist, so fail
                return False
            
            if not self.parent().exists():
                DEBUG and log.error("this is not the root, but the parent directory does not exist")
                return False
            else:
                return self.parent().isWritableFile()
                
                
        myKeyString = self.secretKey.exportKey()    
        fileKeyString = self.getOrSet(elements.PublicKeyString, myKeyString)
        DEBUG and log.error("public key for " + self.fp.path + ": " + fileKeyString)
        return fileKeyString == myKeyString


    def seal(self):
        """
        Sign the meta data and append the signature to
        the meta data.
        
        @param key: an ezPyCrypto key object.
        
        See also: L{ezPyCrypto.key}
        """
        
        DEBUG and log.error("Crypto: sealing " + self.fp.path)
        DEBUG and log.error("Crypto: signable data: " + self.signableMetadata())
        signature = self.secretKey.signString(self.signableMetadata())
        self.deadProperties().set(elements.MetaDataSignature.fromString(signature))
        #storedsignature = self.getOrSet(elements.MetaDataSignature, "0")
        #log.error(signature)
        #log.error(storedsignature)
        DEBUG and log.error("Crypto: signature is " + signature)
        return signature
    
    def updateParent(self, recursionLimit = 0):
        pp = self.parent()
        log.error(pp.fp.path)
        pp and pp.update()

    def _deRegisterWithParent(self):

        DEBUG and log.error("entering _deRegisterWithParent for: " + self.fp.path)
        
        DEBUG and log.error(`self.parent()`)
        pdp = self.parent().deadProperties()
        
        oc = pdp.get(elements.Children.qname()).children
        DEBUG and log.error(len(oc))
        
        DEBUG and log.error("resourceName: " + self.resourceName())     
        nc = [cc for cc in oc if not str(cc.childOfType(rfc2518.HRef)) == self.resourceName()]
        
        pdp.set(elements.Children(*nc))
        DEBUG and log.error("exiting _deRegisterWithParent")
    
    def _registerWithParent(self):

        DEBUG and log.error("entering _registerWithParent for " + self.fp.path)

        DEBUG and log.error("make sure the required properties are initialized")
        self._initProperties()
        
        pdp = self.parent().deadProperties()
        
        oc = pdp.get(elements.Children.qname()).children
        DEBUG and log.error(len(oc))
        
        DEBUG and log.error("resourceName: " + self.resourceName())  
        log.error("foo")   
        DEBUG and log.error("resourceID: " + `self.resourceID()`)    
        for cc in oc:
            DEBUG and log.error("child: " + str(cc.childOfType(rfc2518.HRef)))
            if str(cc.childOfType(rfc2518.HRef)) == self.resourceName():
                DEBUG and log.error(self.fp.path + ": this resource is already registered with the parent")
                return
        
        DEBUG and log.error("foo")
        ic = elements.Child(*[
                         rfc2518.HRef(self.resourceName()),
                         elements.PublicKeyString(self.parent().publicKeyString()),
                         self.resourceID()
                         ])
        DEBUG and log.error("bar")

        
        nc = [cc for cc in oc] + [ic]
        
        log.error(nc)
        ce = elements.Children(*nc)
        log.error(ce.toxml())
        log.error(`pdp`)
        log.error("foobar")
        
        try:
            log.error(self.parent().exists())
            pdp.set(ce)
            log.error("foobar2")
        except:
            import sys, traceback
            msg = apply(traceback.format_exception,sys.exc_info())
            log.error(msg)
            errorMessage = "Unable to update child elements."
            log.error(errorMessage)
            raise
            
            
        log.error("exiting _registerWithParent")
    
        
        
    def _changeRegister(self, request):
        """
        @return a callback that deregisters the current resource and registers the request destination resource.
        """       
        
        from angel_app.resource.local.util import resourceFromURI
        
        def ccCallBack(response):
            self._deRegisterWithParent()
            
            destination_uri = request.headers.getHeader("destination")
            DEBUG and log.error("changeRegister: " + `self.__class__`)
            destination = resourceFromURI(destination_uri, self.__class__)
            destination._registerWithParent()
        
            return response
        
        return ccCallBack

    
    def update(self, recursionLimit = 0):
        
        DEBUG and log.error("called update on: " + self.fp.path)
        
        if not self.isWritableFile(): 
            raise "not authorized to perform update of signed meta data"

        DEBUG and log.error("encrypting " + self.fp.path + "?")
        if self.isEncrypted():
            DEBUG and log.error("encrypting " + self.fp.path)
            self.encrypt()
        DEBUG and log.error("signing " + self.fp.path)
        self.sign()
        DEBUG and log.error("bumping revision number for " + self.fp.path)
        self.bumpRevisionNumber()

        
        DEBUG and log.error("sealing " + self.fp.path)
        self.seal()

        DEBUG and log.error("Verifying " + self.fp.path)
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
        DEBUG and log.error("rendering file in plaintext: " + self.fp.path)
        if self.isEncrypted():
            
            fileContents = self.secretKey.decString(self.fp.open().read())
            return stream.MemoryStream(fileContents, 0, len(fileContents))
        else:
            return Basic.getResponseStream(self)
