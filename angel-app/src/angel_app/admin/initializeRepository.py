import os
 
from angel_app.log import getLogger
from angel_app.config.config import getConfig
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
    # TODO -- we need to be more specific about which key we use for owning the root
    setKey()
    
    from angel_app.admin.resourceProperties import reSign
    log.info("sealing repository root if necessary.")
    # switch to crypto and sign
    reSign()
