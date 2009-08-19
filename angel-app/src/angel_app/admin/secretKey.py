"""
Utilities for creating the default repository directory layout.
"""

import os
import re
from logging import getLogger

from angel_app.config import config
from angel_app.contrib.ezPyCrypto import key as ezKey
from angel_app.singlefiletransaction import SingleFileTransaction

AngelConfig = config.getConfig()
log = getLogger(__name__)

def getKeyringDirectory():
    """
    Returns the fully qualified configured directory name. Makes sure
    that it exists
    """
    directoryname = AngelConfig.get("common","keyring")
    if os.path.exists(directoryname):
        return directoryname
    else:
        raise NameError, "The keyring directory '%s' does not exist" % directoryname

def defaultKeyFilePath():
    return os.path.join(getKeyringDirectory(), "default.key")

def createKey(filePath = defaultKeyFilePath()):
    kk = ezKey()
    # TODO: make key size configurable
    kk.makeNewKeys() 
    log.info("creating new key in file: %r", filePath)
    open(filePath, 'w').write(kk.exportKeyPrivate())
    return kk

def getKeyFor(path = defaultKeyFilePath()):
    """
    @return: the key stored in the supplied file
    """
    angelKey = ezKey()
    angelKey.importKey(open(path).read())
    return angelKey

def getDefaultKey():
    """
    @return: the default key for this node
    """
    return getKeyFor(defaultKeyFilePath())

def defaultPublicKey():
    return getDefaultKey().exportKey()


def createAtLeastOneKey():
    
    # where the keys are located
    keyDirectory = getKeyringDirectory()
    
    # the keys that already exist
    keyFiles = os.listdir(keyDirectory)
    
    log.info("current key files: %r", keyFiles)
    
    # make a key if we don't have any keys yet
    if keyFiles == []:
        createKey()        
        # make sure the new key is globally visible
        reloadKeyRing()

def reloadKeyRing():
    # make sure the new key is globally visible
    # TODO: review: should/must this be in resource.local.internal?
    from angel_app.resource.local.internal import resource
    resource.reloadKeys()

def isValidKey(streamObj):
    """
    checks if the given stream contains a valid key block
    """
    streamObj.seek(0)
    kk = ezKey()
    return kk.importKey(streamObj.read())

def isValidKeyPair(streamObj):
    """
    check sif the given stream contains a key pair (public AND private key)
    """
    kk = ezKey()
    streamObj.seek(0)
    result = False
    if isValidKey(streamObj):
        log.debug("Valid key!")
        streamObj.seek(0)
        if kk.importKey(streamObj.read()):
            log.debug("could import")
            if len(kk.exportKeyPrivate()) > 0:
                log.debug("could export")
                result = True
#    streamObj.seek(0)
    return result

def importKey(streamObj, keyname = "importedkey.key"):
    """
    will try to import the key pair from the given stream object,
    """
    fileextension = ".key"
    # strip off a possibly existing .key extension:
    m = re.compile("\.key$")
    keyname = m.sub('', keyname)
    log.debug("Trying to import a new key")
    if isValidKeyPair(streamObj):
        keyDirectory = getKeyringDirectory()
        newkeyfilename = os.path.join(keyDirectory, keyname + fileextension)
        if os.path.exists(newkeyfilename):
            raise NameError, "A key with the name '%s' already exists" % keyname
        t = SingleFileTransaction()
        newkeyfile = t.open(newkeyfilename, 'wb')
        streamObj.seek(0)
        newkeyfile.write(streamObj.read())
        t.commit()
        reloadKeyRing()
    else:
        raise NameError, "This does not seem to be a valid key-pair!"
    return True
