#from angel_app.static import AngelFile

from os import mkdir
from angel_app.resource.local.internal.resource import Crypto
from angel_app import elements
from angel_app.config.common import rootDir
from angel_app.config import rootDefaults


DEBUG = True

def setupRoot():
    angelRoot = Crypto(rootDir)
    if not angelRoot.fp.exists(): mkdir(rootDir)
    setupRootMetaData()
    
def setupRootMetaData():
    """
    We also want to make sure that the angel app root directory is equipped with
    the proper public key. For now, this means the following: If the root directory
    does not yet have a public key, take the one from config.common.rootDefaults, 
    set the revision number to 1, the content signature to the empty string, and
    sign that.
    
    YOU ONLY NEED THIS IF YOU WANT TO SET UP A NEW ROOT DIRECTORY -- NOT VERY LIKELY,
    I THINK.
    """
    angelRoot = Crypto(rootDir)   
       
    for item in {
                elements.PublicKeyString     :    rootDefaults.publicKey,
                elements.Revision            :    "0",
                elements.Deleted             :    "0"
                }.items():
        angelRoot.getOrSet(item[0], item[1])
    
    # update all remaining metadata
    angelRoot.update()