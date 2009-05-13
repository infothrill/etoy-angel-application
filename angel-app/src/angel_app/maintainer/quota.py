from angel_app.config import config
from angel_app.log import getLogger
from angel_app.resource.local.basic import Basic

log = getLogger(__name__)
AngelConfig = config.getConfig()


class QuotaManager(object):
    def __init__(self, default_, root_, quotas_=None):
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
        quota = None != self.quotas and self.quotas[resource.keyUUID()] or None
        
        if quota is None:
            # no default quota is defined, return default:
            return self.default
        else:
            # quota defined:
            return quota
        
def __readQuotasFromConfig(mounts, quotas):
    mounts = [name for name in mounts.itervalues()]
    
    qq = {}
    
    if quotas is None:
        return qq
    
    for mount in quotas.iterkeys():
        if mount not in mounts:
            log.warn("No mount point defined for quota specification: " + `mount`)
        else:
            myQ = quotas.getint(mount)
            qq[Basic(mount).keyUUID()] = myQ
            log.info("Added quota of " + myQ + " for mount point: " + mount)
            
    return qq

def __createQuotas():
    
    # the default's default: if no default provided, fall back to
    # 100 MB
    oneMeg = 1024 ** 3
    default = 100 * oneMeg
    try:
        default = AngelConfig.getint("common", "defaultquota") 
    except:
        log.warn("No default quota provided. Consider specifying common/defaultquota in the configuration file.")
    log.info("Default quota set to " + `default / oneMeg` + " MiB per mount.")
    
    quotas = None
    try:
        default = AngelConfig.get("quotas")
    except:
        log.warn("No per-mount point quotas specified. Consider specifying a 'quotas' section in the configuration file.")
    
    
    QuotaManager(
                      default,
                      Basic(AngelConfig.get("common", "repository")),
                      __readQuotasFromConfig(
                                             AngelConfig.get("mounttab"),
                                             quotas)
                      )

quotas = __createQuotas()

