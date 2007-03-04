def initializeRepository():
    # create the directory layout
    from angel_app.admin.directories import makeDirectories
    makeDirectories()
    
    # make a secret key, if necessary
    from angel_app.admin.secretKey import createAtLeastOneKey
    createAtLeastOneKey()
    
    # take ownership of repository root
    from angel_app.admin.resourceProperties import setKey
    setKey()
    
    # mount the MISSION ETERNITY root resource
    from angel_app.admin.resourceProperties import setMountPoint
    setMountPoint("", "MISSION ETERNITY", "http://missioneternity.org:9999")
