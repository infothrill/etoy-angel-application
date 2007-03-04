from angel_app.log import getLogger
log = getLogger(__name__)

def initializeRepository():

    from angel_app.admin.directories import makeDirectories
    log.info("initializing repository, if necessary.")
    makeDirectories()
    
    from angel_app.admin.secretKey import createAtLeastOneKey
    log.info("making a secret key, if necessary.")
    createAtLeastOneKey()
    
    from angel_app.admin.resourceProperties import setKey
    log.info("taking ownership of repository root.")
    setKey()
    
    from angel_app.admin.resourceProperties import setMountPoint
    log.info("mounting MISSION ETERNITY")
    from twisted.python.filepath import FilePath
    from angel_app.admin.resourceProperties import absPath
    if not FilePath(absPath("MISSION ETERNITY")).exists():
        setMountPoint("MISSION ETERNITY", "http://missioneternity.org:9999")
