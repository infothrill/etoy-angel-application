from twisted.web2.dav.static import DAVFile
from twisted.python import log
from twisted.web2 import responsecode, dirlist
from twisted.web2.http import HTTPError
from twisted.web2.dav.util import bindMethods
from twisted.web2 import http, stream
from twisted.web2.dav.xattrprops import xattrPropertyStore
from angel_app import elements
from angel_app.angelMixins import deletable, putable
from ezPyCrypto import key as ezKey

DEBUG = False

class AngelFile(DAVFile, deletable.Deletable, putable.Putable):
    """
    In addition to providing WebDAV functionality (file system operations
    over the network), this class also implements encryption and metadata
    management.
    """
    
    secretKey = None
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        DAVFile.__init__(self, path, defaultType, indexNames)
    
    def davComplianceClasses(self):
        """
        We fake level 2 compliance, to be able to run with OS X 10.4 's 
        builtin dav client. Adding locking via xattr should be relatively
        straightforward, though.
        """
        return ("1", "2") # Add "2" when we have locking

    def deadProperties(self):
        """
        Provides internal access to the WebDAV dead property store.  You
        probably shouldn't be calling this directly if you can use the property
        accessors in the L{IDAVResource} API instead.  However, a subclass must
        override this method to provide it's own dead property store.

        This implementation returns an instance of L{NonePropertyStore}, which
        cannot store dead properties.  Subclasses must override this method if
        they wish to store dead properties.

        @return: a dict-like object from which one can read and to which one can
            write dead properties.  Keys are qname tuples (ie. C{(namespace, name)})
            as returned by L{davxml.WebDAVElement.qname()} and values are
            L{davxml.WebDAVElement} instances.
        """
        if not hasattr(self, "_dead_properties"):
            self._dead_properties = xattrPropertyStore(self)
        return self._dead_properties
    
    
    def encrypt(self):
        """
        Replace the contents of the file with the encrypted data.
        
        TODO: this implementation is dog slow and non-atomic. Revamp.
        """
        
        if self.fp.isdir(): return
        
        myFile = self.fp.open() 
        plainText = myFile.read()
        myFile.close()
        cypherText = self.secretKey.encString(plainText)
        DEBUG and log.err("encrypting file")
        myFile = self.fp.open("w") 
        myFile.write(cypherText)
        myFile.close()  

    def sign(self):
        """
        Sign the file contents and store the public key and signature in the metadata.
        """
        
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

    def getOrSet(self, davXmlTextElement, defaultValueString = ""):
        
        if not self.fp.exists():
            DEBUG and log.err("AngelFile.getOrSet: file not found for path: " + self.fp.path)
            raise HTTPError(responsecode.NOT_FOUND)
        
        dp = self.deadProperties()
        try:
            element = dp.get(davXmlTextElement.qname())
            #data = element.children[0].data
            data = "".join([c.data for c in element.children])
            DEBUG and log.err("AngelFile.getOrSet: data for " + `davXmlTextElement.qname()` + ": " + data)
            self.fp.restat()
            return data
        except HTTPError:
            DEBUG and log.err("AngelFile.getOrSet: initializing element " + `davXmlTextElement.qname()` + " to " + defaultValueString)
            dp.set(davXmlTextElement.fromString(defaultValueString))
            self.fp.restat()
            return defaultValueString

        
        
    def revisionNumber(self):
        return int(self.getOrSet(elements.Revision, "0"))


    def bumpRevisionNumber(self):
        """
        Increase the revision number by one, if it not initialized, set it to 1.
        """
        nn = self.revisionNumber() + 1
        DEBUG and log.err("revision number for " + self.fp.path +" now at: " + `nn`)
        self.deadProperties().set(elements.Revision.fromString(`nn`))
        return int(nn)
    
    def isDeleted(self):
        """
        """
        vv = self.getOrSet(elements.Deleted, "0")
        id = (vv != "0")       
        DEBUG and log.err("AngelFile.isDeleted(): " + vv + ": " + `id`)
        return vv != "0"

    def publicKeyString(self):
        try:
            return self.deadProperties().get(elements.PublicKeyString.qname())           
        except:
            # no key set yet -- maybe we have a key handy for signign?
            try:
                keyString = self.secretKey.exportKey()
                DEBUG and log.err("initializing public key to: " + keyString)
                return self.getOrSet(elements.PublicKeyString, keyString) 
            finally:
                raise HTTPError(responsecode.FORBIDDEN)
        

    def isWritableFile(self):
        """
        A file is writable, if we're the owner of that file, i.e. if
        the signing key associated with the file is our local public key.
        
        Alternatively, if the file does not exist yet, it's considered writable if 
        the parent directory exists and is writable.
        
        @returns True if the location is writable, False otherwise
        """
        
        if not self.secretKey:
            # we don't even have a private key
            DEBUG and log.err("no key available")
            return False
        
        myKeyString = self.secretKey.exportKey()
        
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
        fileKeyString = self.getOrSet(elements.PublicKeyString, myKeyString)
        bb = (fileKeyString == myKeyString)
        if not bb:
            DEBUG and log.err("isWritableFile: not writable: " + self.fp.path)
            DEBUG and log.err("fileKey: " + fileKeyString)
            DEBUG and log.err("myKey: " + myKeyString)
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
        self.encrypt()
        self.sign()
        self.bumpRevisionNumber()
        self.seal()
        # for debugging
        self.verify()
        
        # certainly not going to hurt if we do this:
        self.fp.restat()
        
        log.err(self.fp.path + " now at revision: " + self.getOrSet(elements.Revision)) 
    
    def verify(self):
        
        publicKey = ezKey()
        publicKey.importKey(self.getOrSet(elements.PublicKeyString))

        contentSignature = self.getOrSet(elements.ContentSignature, "")
        DEBUG and log.err("verify(): signature: " + contentSignature)
        dataIsCorrect = publicKey.verifyString(
                                  self.fp.open().read(),
                                  contentSignature)
        DEBUG and log.err("data signature for file " + self.fp.path + " is correct: " + `dataIsCorrect`)
            
        metaDataIsCorrect = publicKey.verifyString(
                                  self.signableMetadata(),
                                  self.getOrSet(elements.MetaDataSignature))
        
        DEBUG and log.err("meta data signature for file " + self.fp.path + " is correct: " + `metaDataIsCorrect`)
            
        return dataIsCorrect and metaDataIsCorrect

    def render(self, req):
        """You know what you doing. override render method (for GET) in twisted.web2.static.py"""
        if not self.fp.exists():
            return responsecode.NOT_FOUND

        if self.fp.isdir():
            return self.renderDirectory(req)

        return self.renderFile()

    def renderDirectory(self, req):
        if req.uri[-1] != "/":
            # Redirect to include trailing '/' in URI
            return http.RedirectResponse(req.unparseURL(path=req.path+'/'))
        else:
            ifp = self.fp.childSearchPreauth(*self.indexNames)
            if ifp:
                # Render from the index file
                standin = self.createSimilarFile(ifp.path)
            else:
                # Render from a DirectoryLister
                standin = dirlist.DirectoryLister(
                    self.fp.path,
                    self.listChildren(),
                    self.contentTypes,
                    self.contentEncodings,
                    self.defaultType
                )
            return standin.render(req)


    def renderFile(self):
        
        log.err("running renderFile")
        
        try:
            f = self.fp.open()
        except IOError, e:
            import errno
            if e[0] == errno.EACCES:
                return responsecode.FORBIDDEN
            elif e[0] == errno.ENOENT:
                return responsecode.NOT_FOUND
            else:
                raise
        
        response = http.Response()
        # vincent: slurp and decrypt the file, then make a memory 
        # stream out of it
        #response.stream = stream.FileStream(f, 0, self.fp.getsize())
        # TODO: very inefficient and unsafe
        # the proper way to proceed would be the following:
        # check if the file is encrypted (should be an xattr flag),
        # if it is, decrypt, otherwise return the file right away.
        try:
            fileContents = self.secretKey.decString(self.fp.open().read())
            response.stream = stream.MemoryStream(fileContents, 0, len(fileContents))
            
        except:
            log.err("missing key for file: " + self.fp.path + "returning cyphertext")
            response.stream = stream.FileStream(f, 0, self.fp.getsize())
            
        
        
        for (header, value) in (
            ("content-type", self.contentType()),
            ("content-encoding", self.contentEncoding()),
        ):
            if value is not None:
                response.headers.setHeader(header, value)
        
        return response

#
# Attach method handlers to DAVFile
#
import angel_app.method
bindMethods(angel_app.method, AngelFile)


def py2AppWorkaroundIgnoreMe():
    try:
        from angel_app.method import delete, lock, propfind, put
    except: pass
