"""
Utilities for creating the default repository directory layout.
"""

import os
from angel_app.config import config

AngelConfig = config.getConfig()

def createKey(filePath = os.path.join(AngelConfig.get("common","keyring"), "default.key")):
    kk = ezKey()
    # TODO: make key size configurable
    kk.makeNewKeys() 
    open(filePath, 'w').write(kk.exportKeyPrivate())

def createAtLeastOneKey():
    from angel_app.contrib.ezPyCrypto import key as ezKey
    
    # where the keys are located
    keyDirectory = AngelConfig.get("common", "keyring")
    
    # the keys that already exist
    keyFiles = os.listdir(keyDirectory)
    
    # make a key if we don't have any keys yet
    if keyFiles == []:
        createKey()
