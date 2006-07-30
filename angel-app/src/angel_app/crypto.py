from ezPyCrypto import key as ezKey
from os import sep, environ

keyBase = sep.join([
                    environ["HOME"],
                    ".angel_app",
                    "keyring"
                    ])

#def loadKeysFromFile(): pass

def loadKeysFromFile(fileName = ""):
    """
    Load the ***SECRET*** keys from the appropriate location in the angel-app directory.
    """
    angelKey = ezKey()                                             
    angelKey.importKey(
                     open(
                       sep.join([keyBase, "key.private"])
                       ).read()
                       )    
    return angelKey