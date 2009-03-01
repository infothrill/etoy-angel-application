from angel_app.config import config
from angel_app.graph import graphWalker
from angel_app.log import getLogger
from angel_app.maintainer import sync
from angel_app.maintainer import update
from angel_app.resource import childLink
from angel_app.resource.local.basic import Basic
import os
import time

log = getLogger(__name__)
AngelConfig = config.getConfig()

quotas = QuotaManager(
                      AngelConfig.getint("common", "defaultquota"),
                      Basic(AngelConfig.get("common","repository")),
                      __readQuotasFromConfig(
                                             AngelConfig.get("mounttab"),
                                             AngelConfig.get("quotas"))
                      )
        
def __readQuotasFromConfig(mounts, quotas):
    mounts = [name for name in mounts.itervalues()]
    
    qq = {}
    for mount in config.iterkeys():
        if mount not in mounts:
            log.warn("No mount point defined for quota specification: " + `mout`)
        else:
            myQ = config.getint(mount)
            qq[Basic(mount).keyUUID()] = myQ
            log.info("Added quota of "  + myQ + " for mount point: " + mount)
            
    return qq
            
        
        
    
class QuotaManager:
    def __init__(self, default_, root_, quotas_):
        self.default = default_
        self.root = root_
        self.quotas = quotas_

    
    def quota(self, resource):
        """
        @return: the quota in bytes for the mount point on which this resource
        is mounted. Zero if no quota.
        
        Note the following special cases:
        * the root resource and its direct children (i.e. those resources having the
        same owner as the root resource) have no quota,
        * for all other resources, a global default quota is provided
        """
        if resource.keyUUID() == self.root.keyUUID():
            # resource is part of local resources -- don't apply a quota
            return 0
        
        # otherwise, it's a mounted resource
        quota = self.quotas[resource.keyUUID()]
        
        if quota is None:
            # no default quota is defined, return default:
            return self.default
        else:
            # quota defined:
            return quota