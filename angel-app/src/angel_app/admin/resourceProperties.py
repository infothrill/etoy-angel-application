"""
Utility script to force resigning the repository root
"""

import angel_app.resource.local.internal.resource.Crypto as Crypto
from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common", "repository")

from angel_app.config import internal
secretKeys = internal.loadKeysFromFile()

def absPath(relativePathInRepository):
    return os.path.join(AngelConfig.get("common","angelhome"), relativePathInRepository)
            
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
    r = Crypto(absPath(path))
    r.deadProperties().set(PublicKeyString(key.exportKey()))
    reSign(path)
    
def setMountPoint(
                  mountPoint = "MISSION ETERNITY", 
                  URLToMount = "http://missioneternity.org:9999"):
    """
    @param path is the resource that we want to use as a mount point
    @param pointsTo is the URL of the resource that we want to mount
    """
    import urlparse
    
    import os
    
    pp = absPath(mountPoint)
    
    assert not os.exits(pp), "Can't create mount point where resource exists: " + pp
    
    from angel_app.resource.remote import clone
    
    # TODO:
    # urlparse is unfortunately still kind of broken in 2.4 (2.5 is fine),
    # so we have to
    url = urlparse.urlparse(URLToMount)
    host, path = url[1], url[2]
    path, port = path.split(":")
    if port == "": 
        # TODO: check: does this give the default port (9999 <- we want this) 
        # or the port used on this host?
        port = providerport = AngelConfig.getint("provider","listenPort")
        
    cc = clone.Clone(host, path, int(port))
    
    if not (cc.ping() and cc.exists()):
        raise clone.CloneNotFoundError(
                   "Can not connect to %s. Can not initialize mount point." % URLToMount)
    

    # --- the local mount point can be initialized ---
    
    # create the mount point  
    from angel_app import elements      
    os.mkdir(pp)    
    rr = Crypto(pp)
    
    # initialize all required properties -- rubbish is ok for many of them,
    # as long as we clearly state that ${URLToMount} is the original:  
    rr.deadProperties().set(
                            elements.PublicKeyString(
                                 cc.publicKeyString()))
    
    rr.deadProperties().set(
                            elements.ResourceID(cc.resourceID()))
    
    rr._registerWithParent()
    
    # add the clone
    rr.deadProperties.set(clonesToElement([cc]))
    