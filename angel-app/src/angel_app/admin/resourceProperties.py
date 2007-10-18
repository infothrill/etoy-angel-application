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
    return os.path.join(AngelConfig.get("common","repository"), relativePathInRepository)
            
def reSign(path = ""):
    """
    Request new signing of resource.
    Path is a relative path with respect to repository root.
    """
    rr = Crypto(absPath(path))
    if not rr.verify():
        rr.sign()
        rr.seal()

def setKey(path = "", key = secretKeys.values()[0]):
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
        
    
def setMountPoint(mountPoint, URLToMount):
    """
    @param path is the resource that we want to use as a mount point
    @param pointsTo is the URL of the resource that we want to mount
    """       
    log.info("attempting to mount: " + URLToMount + " at " + mountPoint)
    import urlparse
    
    pp = absPath(mountPoint)
    
    assert not os.path.exists(pp), "Can't create mount point where resource exists: " + pp
    
    from angel_app.resource.remote import clone
    

    # TODO:urlparse is unfortunately still kind of broken in 2.4 (2.5 is fine),
    # so we have to
    url = urlparse.urlparse(URLToMount)
    host, path = url[1], url[2]
    if path == "":
        path = "/"
    
    host, port = host.split(":")
    if port == "": 
        from angel_app.config.defaults import providerPublicListenPort # default port of other peers
        port = providerPublicListenPort
        
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
                                                rr._computeContentHexDigest() ))
    
    dp.set(elements.ResourceID(
                               cc.resourceID()))
    
    rr._registerWithParent()
   
    # add the clone
    from angel_app.resource.remote.clone import clonesToElement
    # TODO: check that the resource is already registered -- might happen in special cases
    dp.set(clonesToElement([cc]))
          
    from angel_app.resource.remote.client import inspectResource
    inspectResource(rr)
    
