from angel_app.log import getLogger
from angel_app.config.config import getConfig
log = getLogger(__name__)

def getMountTab():
    angelConfig = getConfig()
    mounttab = []
    if angelConfig.has_section('mounttab'):
        for device in angelConfig.get('mounttab').keys():
            mounttab.append( (device, angelConfig.get('mounttab', device) ) )

    if len(mounttab) < 1:
        log.debug("No mounts configured in mounttab in configuration")
    return mounttab

def initializeRepository():

    from angel_app.admin.directories import makeDirectories
    log.info("initializing repository, if necessary.")
    makeDirectories()
    
    from angel_app.admin.secretKey import createAtLeastOneKey
    log.info("making a secret key, if necessary.")
    createAtLeastOneKey()
    
    from angel_app.admin.resourceProperties import setKey
    log.info("taking ownership of repository root.")
    # TODO -- we need to be more specific about which key we use for owning the root
    setKey()
    
    from angel_app.admin.resourceProperties import reSign
    log.info("sealing repository root if necessary.")
    # switch to crypto and sign
    reSign()
    
    from angel_app.admin.resourceProperties import setMountPoint
    from twisted.python.filepath import FilePath
    from angel_app.admin.resourceProperties import absPath
    
    fstab = getMountTab()
    for mount in fstab:
        log.info("mounting '%s' to '%s'" % (mount[0], mount[1]))
        if not FilePath(absPath(mount[1])).exists():
            setMountPoint(mount[1], mount[0])
