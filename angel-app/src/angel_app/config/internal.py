from angel_app.contrib.ezPyCrypto import key as ezKey
from os import sep, listdir

from angel_app.config.config import getConfig
from angel_app.log import getLogger

log = getLogger(__name__)
angelConfig = getConfig()

keyBase = angelConfig.get("common", "keyring")

# TODO: it seems odd to have one module for a single function. review.

def loadKeysFromFile(keyDir = keyBase):
    """
    Load the ***SECRET*** keys from the appropriate location in the angel-app directory.
    """
    
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

