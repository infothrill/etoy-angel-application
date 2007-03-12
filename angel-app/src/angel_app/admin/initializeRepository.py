from angel_app.log import getLogger
log = getLogger(__name__)

fstab = [
         ["http://missioneternity.org:6221", "MISSION ETERNITY"]
         ]

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
    reSign(path)
    
    from angel_app.admin.resourceProperties import setMountPoint
    from twisted.python.filepath import FilePath
    from angel_app.admin.resourceProperties import absPath

    for mount in fstab:
        log.info("mounting '%s' to '%s'" % (mount[0], mount[1]))
        if not FilePath(absPath(mount[1])).exists():
            setMountPoint(mount[1], mount[0])
