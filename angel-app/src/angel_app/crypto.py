from ezPyCrypto import key as ezKey
from os import sep, environ

keyBase = sep.join([
                    environ["HOME"],
                    ".angel_app",
                    "keyring"
                    ])

#def loadKeysFromFile(): pass

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