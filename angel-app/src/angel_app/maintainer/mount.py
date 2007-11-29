import os
 
from angel_app.log import getLogger
from angel_app.config.config import getConfig
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

def addMounts():
    
    from angel_app.admin.resourceProperties import setMountPoint
    from angel_app.admin.resourceProperties import absPath
    
    fstab = getMountTab()
    for mount in fstab:
        log.info("mounting '%s' to '%s'" % (mount[0], mount[1]))
        if not os.path.exists(absPath(mount[1])):
            setMountPoint(mount[1], mount[0])
