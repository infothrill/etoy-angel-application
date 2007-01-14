#from angel_app.static import AngelFile

from os import mkdir
from angel_app.resource.local.internal.resource import Crypto
from angel_app import elements
from angel_app.config import rootDefaults
from twisted.python import log

DEBUG = True

# get config:
from angel_app.config import config
AngelConfig = config.Config()
repository = AngelConfig.get("common","repository")

def setupRoot():
    angelRoot = Crypto(repository)
    if not angelRoot.fp.exists(): mkdir(repository)
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
    angelRoot = Crypto(repository)
    DEBUG and log.err("public key: " + rootDefaults.publicKey)
       
    for item in [
                elements.PublicKeyString(rootDefaults.publicKey),
                elements.Revision("0"),
                elements.Encrypted("0")
                ]:
        if not angelRoot.hasDeadProperty(item.qname()):
            angelRoot.deadProperties().set(item)
    
    # update all remaining metadata
    angelRoot.update()