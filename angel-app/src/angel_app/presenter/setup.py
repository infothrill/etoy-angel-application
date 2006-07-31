from angel_app.static import AngelFile
from angel_app import elements
from config.common import rootDir
from config import rootDefaults


DEBUG = True

    
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
 
    angelRoot = AngelFile(rootDir)   
    for item in {
                elements.PublicKeyString     :    rootDefaults.publicKey,
                elements.Revision            :    "0",
                elements.Deleted             :    "0"
                }.items():
        angelRoot.getOrSet(item[0], item[1])
    
    # update all remaining metadata
    angelRoot.update()