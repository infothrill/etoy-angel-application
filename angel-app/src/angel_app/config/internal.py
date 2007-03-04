from angel_app.contrib.ezPyCrypto import key as ezKey
from os import sep, listdir

from angel_app.config.config import getConfig

angelConfig = getConfig()

keyBase = angelConfig.get("common", "keyring")

def loadKeysFromFile(keyDir = keyBase):
    """
    Load the ***SECRET*** keys from the appropriate location in the angel-app directory.
    """
    
    from angel_app.log import getLogger
    # TODO: which argument to give to getLogger, if we don't know which process we're getting called from?
    log = getLogger()
    
    keyFiles = listdir(keyDir)
    keyRing = {}
    for fileName in keyFiles:
        log.info("loading secret key: " + `fileName`)
        angelKey = ezKey()                                             
        angelKey.importKey(
                     open(
                       keyDir + sep + fileName
                       ).read()
                       ) 
        keyRing[angelKey.exportKey()] = angelKey
    return keyRing

from angel_app import elements
from angel_app.resource.local.internal import util
defaultMetaData = {
                   elements.Revision           : lambda x: "0",
                   elements.Encrypted          : lambda x: "0",
                   elements.PublicKeyString    : lambda x: x.parent() and x.parent().publicKeyString() or "",
                   elements.ContentSignature   : lambda x: "",
                   elements.ResourceID         : lambda x: util.makeResourceID(x.relativePath()) 
                   }
