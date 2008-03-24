"""
Utility script to force resigning the repository root
"""
import os

from angel_app.log import getLogger
log = getLogger(__name__)

from angel_app.resource.local.basic import Basic
from angel_app.resource.local.internal.resource import Crypto
from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common", "repository")

from angel_app.config import internal
secretKeys = internal.loadKeysFromFile()

def absPath(relativePathInRepository):
    """
    Given the path relative to the repository root, return the absolute path on the file system.
    """
    
    # workaround for os.path.join "feature"
    rp = relativePathInRepository.lstrip(os.sep)
    if "" == rp:
        return repository
    else:
        return os.path.join(repository, rp)
            
def reSign(path = ""):
    """
    Request new signing of resource.
    Path is a relative path with respect to repository root.
    """
    rr = Crypto(absPath(path))
    if not rr.verify():
        rr._signContent()
        rr.seal()

def setKey(path = "", key = None):
    if key is None: # fetch default key
        key = secretKeys.values()[0]
    from angel_app.elements import PublicKeyString
    # first set the key -- this won't work with Crypto
    rr = Basic(absPath(path))
    try:
        presentKey = rr.publicKeyString()
    except:
        log.info("no key set for " + path)
        presentKey = ""

    try: 
        key.importKey(presentKey)
        log.info("key already set to %s for resource: %s"  % (presentKey, rr.fp.path))
    except:       
        rr.deadProperties().set(PublicKeyString(key.exportKey()))
    
