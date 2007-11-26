"""
Routines for obtaining a best guess about the current replication state of a clone. 
"""


from angel_app.config import config
from angel_app.log import getLogger
import copy
import random

log = getLogger(__name__)
AngelConfig = config.getConfig()
maxclones = AngelConfig.getint("common","maxclones")

class CloneLists(object):
    def __init__(self):
        self.good = []
        self.old = []
        self.unreachable = []
        self.bad = []

def accessible(clone):
    """
    Check if the clone is reachable, resolve redirects.
    """
    if not clone.ping():
        log.debug("iterateClones: clone " + `clone` + " not reachable, ignoring")
        return (clone, False)
        
    clone = clone.checkForRedirect()
        
    if not clone.exists():
        log.debug("iterateClones: resource " + `clone.path` + " not found on host " + `clone.host`)
        return (clone, False)
    
    return (clone, True)

def iterateClones(cloneSeedList, publicKeyString, resourceID):
    """
    get all the clones of the (valid) clones we have already looked at
    which are not among any (including the invalid) of the clones we
    have already looked at, and validate those clones.
    
    @rtype ([Clone], [Clone])
    @return a tuple of ([the list of valid clones], [the list of checked clones])
    """  
    toVisit = copy.copy(cloneSeedList)
    visited = []
    cl = CloneLists()
    revision = 0
    
    while len(toVisit) != 0:
        # there are clones that we need to inspect
        
        # pop the next clone from the queue
        cc = toVisit[0]
        log.debug("inspecting clone: " + `cc`)
        toVisit = toVisit[1:]
        
        if cc in visited:
            # we have already looked at this clone -- don't bother with it
            log.debug("iterateClones: " + `cc` + " already visited, ignoring")
            continue
               
        # otherwise, mark the clone as checked and proceed
        visited.append(cc)
        
        if not cc.ping():
            log.debug("iterateClones: clone " + `cc` + " not reachable, ignoring")
            cl.unreachable.append(cc)
            continue
        
        cc = cc.checkForRedirect()
        
        if not cc.exists():
            log.debug("iterateClones: resource " + `cc.path` + " not found on host " + `cc`)
            cl.bad.append(cc)
            continue
        
        if cc.resourceID() != resourceID:
            # an invalid clone
            log.debug("iterateClones: " + `cc` + " wrong resource ID")
            log.debug("expected: " + `resourceID`)
            log.debug("found: " + `cc.resourceID()`)
            cl.bad.append(cc)
            continue
        
        if cc.publicKeyString() != publicKeyString:
            # an invalid clone
            log.debug("iterateClones: " + `cc` + " wrong public key")
            log.debug("expected: " + publicKeyString)
            log.debug("found: " + cc.publicKeyString())
            cl.bad.append(cc)
            continue
        
        if not cc.validate():
            # an invalid clone
            log.debug("iterateClones: " + `cc` + " invalid signature")
            cl.bad.append(cc)
            continue
        
        rr = cc.revision()
        
        if rr < revision:
            # too old
            log.debug("iterateClones: " + `cc` + " too old: " + `rr` + " < " + `revision`)
            if cc not in cl.old:
                cl.old.append(cc)
            continue
        
        if rr > revision:
            # hah! the clone is newer than anything
            # we've seen so far. all the clones we thought
            # were good are in fact bad.
            log.debug("iterateClones: " + `cc` + " very new: " + `rr` + " > " + `revision`)
            cl.old.extend(cl.good)
            cl.good = []
            revision = rr
        
        # we only arrive here if the clone is valid and sufficiently new
        cl.good.append(cc)
        log.debug("iterateClones: adding good clone: " + `cc`)
        log.debug(`cc.cloneList()`)
        toVisit += cc.cloneList()
        
        

    log.info("iterateClones: good clones: " + `cl.good`)
    log.info("iterateClones: bad clones: " + `cl.bad`)
    
    return cl
    
def eliminateSelfReferences(clones):
    selfReferences = ["localhost", "127.0.0.1", AngelConfig.get("maintainer","nodename")]
    return [cc for cc in clones if cc.host not in selfReferences] 

def clonesToStore(goodClones, unreachableClones):
    """
    We're interested in storing a (maximum number) of clones of "sufficient quality".
    The "better" a clone, the more we would like to keep it. What is "good" in this context?
    If we've just validated a clone (i.e. it's a member of the goodClones list), that should
    certainly count as good. However, in the case were we have few good clones, 
    we might even want to store clones that were unreachable -- after all, perhaps the host
    they're on was just temporarily offline?
    
    @param af: the local resource
    @param goodClones: good clones of this resource
    @param unreachableClones: unreachableClones of this resource
    
    @see:  iterateClones
    """
    
    # set up a queue of good clones and unreachable clones, both in randomized sequence
    gc = copy.copy(eliminateSelfReferences(goodClones))
    random.shuffle(gc)
    
    uc = copy.copy(eliminateSelfReferences(unreachableClones))
    random.shuffle(uc)
    
    clonesWeMightStore = gc + uc

    # fill in only non-duplicates    
    clonesToBeStored = []    
    for clone in clonesWeMightStore:
        # take only non-duplicates
        if clone not in clonesToBeStored:
            clonesToBeStored.append(clone)
            
        # guard against DOS and xattr overflow
        if len(clonesToBeStored) >= maxclones: break

    return clonesToBeStored