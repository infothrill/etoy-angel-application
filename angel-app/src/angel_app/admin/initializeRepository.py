log = getLogger("admin." + __name__)

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
    setMountPoint("MISSION ETERNITY", "http://missioneternity.org:9999")
