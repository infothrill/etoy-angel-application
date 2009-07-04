from os import sep, listdir

from angel_app.config.config import getConfig
from angel_app.log import getLogger
from angel_app.admin import secretKey


log = getLogger(__name__)
angelConfig = getConfig()

# TODO: it seems odd to have one module for a single function. review.
# fix: should go into admin/secretKey

def loadKeysFromFile(keyDir = secretKey.getKeyringDirectory()):
    """
    Load the ***SECRET*** keys from the appropriate location in the angel-app directory.
    """ 
    keyFiles = listdir(keyDir)
    keyRing = {}
    for fileName in keyFiles:
        log.info("loading secret key: %r", fileName)
        angelKey = secretKey.getKeyFor(keyDir + sep + fileName)
        keyRing[angelKey.exportKey()] = angelKey
    return keyRing

