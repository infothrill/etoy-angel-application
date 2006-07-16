from ezPyCrypto import key as ezKey
from pickle import load
from os import sep, environ

keyBase = sep.join([
                    environ["HOME"],
                    ".angel_app",
                    "keyring"
                    ])

def loadKeysFromFile():
    """
    Load the keys from the appropriate location in the meat directory.
    """
    angelKey = ezKey()                                             
    angelKey.importKey(
                     open(
                       sep.join([keyBase, "key.private"])
                       ).read()
                       )    
    return angelKey
