port = 9998
interface = "127.0.0.1"

from angel_app.contrib.ezPyCrypto import key as ezKey
from os import sep, environ

keyBase = sep.join([
                    environ["HOME"],
                    ".angel_app",
                    "keyring"
                    ])

def loadKeysFromFile(fileName = sep.join([keyBase, "key.private"])):
    """
    Load the ***SECRET*** keys from the appropriate location in the angel-app directory.
    """
    angelKey = ezKey()                                             
    angelKey.importKey(
                     open(
                       fileName
                       ).read()
                       )    
    return angelKey

from angel_app import elements
from angel_app.resource.local.internal import util
defaultMetaData = {
                   elements.Revision           : lambda x: "0",
                   elements.Encrypted          : lambda x: "0",
                   elements.PublicKeyString    : lambda x: x.parent() and x.parent().publicKeyString() or "",
                   elements.ContentSignature   : lambda x: "",
                   elements.ResourceID         : lambda x: util.makeResourceID(x.relativePath()) 
                   }
