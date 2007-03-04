"""
Utility script to force resigning the repository root
"""

from angel_app.log import getLogger
log = getLogger(__name__)

import os
from angel_app.resource.local.basic import Basic
from angel_app.resource.local.internal.resource import Crypto
from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common", "repository")

from angel_app.config import internal
secretKeys = internal.loadKeysFromFile()

def absPath(relativePathInRepository):
    return os.path.join(AngelConfig.get("common","repository"), relativePathInRepository)
            
def reSign(path = ""):
    """
    Force new signing of resource.
    Path is a relative path with respect to repository root.
    """
    r = Crypto(absPath(path))
    r.sign()
    r.seal()

def setKey(path = "", key = secretKeys.values()[0]):
    from angel_app.elements import PublicKeyString
    # first set the key -- this won't work with Crypto
    rr = Basic(absPath(path))
    try:
        rr.publicKeyString()
        return
    except:
        log.info("setting key for " + path + " to " + key.exportKey())
        rr.deadProperties().set(PublicKeyString(key.exportKey()))
        # switch to crypto and sign
        reSign(path)
    
def setMountPoint(
                  mountPoint = "MISSION ETERNITY", 
                  URLToMount = "http://missioneternity.org:9999"):
    """
    @param path is the resource that we want to use as a mount point
    @param pointsTo is the URL of the resource that we want to mount
    """       
    log.info("attempting to mount: " + URLToMount + " at " + mountPoint)
    import urlparse
    
    import os
    
    pp = absPath(mountPoint)
    
    assert not os.path.exists(pp), "Can't create mount point where resource exists: " + pp
    
    from angel_app.resource.remote import clone
    

    # TODO:
    # urlparse is unfortunately still kind of broken in 2.4 (2.5 is fine),
    # so we have to
    url = urlparse.urlparse(URLToMount)
    host, path = url[1], url[2]
    if path == "":
        path = "/"
    
    host, port = host.split(":")
    if port == "": 
        # TODO: check: does this give the default port (9999 <- we want this) 
        # or the port used on this host?
        port = providerport = AngelConfig.getint("provider","listenPort")
        
    cc = clone.Clone(host, int(port), path)
    
    if not (cc.ping() and cc.exists()):
        # don't fail, just mount at next startup
        log.warn("Can not connect to %s. Can not initialize mount point." % URLToMount)
        return
    

    # --- the local mount point can be initialized ---
    log.info("mount point and clone OK, proceeding to mount.")
    
    # create the mount point  
    from angel_app import elements      
    os.mkdir(pp)    
    rr = Crypto(pp)
    
    # initialize all required properties -- rubbish is ok for many of them,
    # as long as we clearly state that ${URLToMount} is the original:  
    dp = rr.deadProperties()
    dp.set(elements.PublicKeyString(
                                 cc.publicKeyString()))
    
    dp.set(elements.MetaDataSignature(
                                 cc.metaDataSignature()))
    
    dp.set(elements.ContentSignature.fromString(
                                                self._computeContentHexDigest() ))
    
    dp.set(elements.ResourceID(
                               cc.resourceID()))
    
    rr._registerWithParent()
    
    # add the clone
    from angel_app.resource.remote.clone import clonesToElement
    dp.set(clonesToElement([cc]))
    
