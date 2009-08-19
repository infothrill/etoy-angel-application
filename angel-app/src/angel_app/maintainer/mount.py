import os
from logging import getLogger

from angel_app.admin.resourceProperties import absPath
from angel_app.config.config import getConfig
from angel_app.resource.local.basic import Basic
from angel_app.resource.local.internal.resource import Crypto
 
log = getLogger(__name__)

def getMountTab():
    """
    Fetches the configured mounts and returns a 2 dimensional list with
    device - mountpoint values.
    
    @return: list of lists
    """
    angelConfig = getConfig()
    mounttab = []
    if angelConfig.has_section('mounttab'):
        for device in angelConfig.get('mounttab').keys():
            mounttab.append( (device, angelConfig.get('mounttab', device) ) )

    if len(mounttab) < 1:
        log.debug("No mounts configured in mounttab in configuration")
    return mounttab

        
    
def setMountPoint(mountPoint, URLToMount):
    """
    @param path is the resource that we want to use as a mount point
    @param pointsTo is the URL of the resource that we want to mount
    """       
    log.info("attempting to mount: %s at %s", URLToMount, mountPoint)
    
    pp = absPath(mountPoint)
    
    from angel_app.resource.remote import clone
    
    cc = clone.cloneFromURI(URLToMount)
    
    if not (cc.ping() and cc.exists()):
        # don't fail, just mount at next startup
        log.warn("Can not connect to %s. Can not initialize mount point.", URLToMount)
        return
    

    # --- the local mount point can be initialized ---
    log.info("mount point and clone OK, proceeding to mount.")
    
    # create the mount point, if necessary
    if not os.path.exists(pp):
        os.mkdir(pp)
    else:
        assert Basic(pp).isCollection(), "Mount point must be a directory."
        
    rr = Crypto(pp)

    from angel_app import elements    
    # initialize all required properties -- rubbish is ok for many of them,
    # as long as we clearly state that ${URLToMount} is the original:  
    dp = rr.deadProperties()
    dp.set(elements.PublicKeyString.fromString(
                                 cc.publicKeyString()))
    
    dp.set(elements.MetaDataSignature.fromString(
                                 cc.metaDataSignature()))
    
    dp.set(elements.ContentSignature.fromString(
                                                rr._computeContentHexDigest() ))

    
    rid = cc.resourceID()
    lid = elements.ResourceID.fromString(rid)
    dp.set(lid)
    
    rr._registerWithParent()
   
    # add the clone
    from angel_app.resource.remote.clone import clonesToElement
    # here, we store a list of already known clones + the remote mount !
    # this makes sure that it works both for the first virgin mount as well as later
    dp.set(clonesToElement(rr.clones() + [cc]))
          
    from angel_app.maintainer.client import inspectResource
    
    try:
        inspectResource(rr)
    except KeyboardInterrupt:
        raise
    except Exception, e:
        log.warn("Resource inspection failed for mount point: %s", pp, exc_info = e)

def addMounts():
    
    fstab = getMountTab()
    for mount in fstab:
        ap = absPath(mount[1])
        log.info("Attempting to mount %s at %s (in repository) => %s (on file system).", mount[0], mount[1], ap)
        bb = Basic(ap)
        if (not bb.exists()) or (not bb.validate()):
            log.info("mounting '%s' to '%s'", mount[0], mount[1])
            try:
                setMountPoint(mount[1], mount[0])
            except Exception, e:
                log.warn("Mount failed for %r", mount[1], exc_info = e)
