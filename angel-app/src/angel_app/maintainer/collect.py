"""
Routines for obtaining a best guess about the current replication state of a clone. 
"""


from angel_app.config import config
from angel_app.log import getLogger
import copy
import itertools
import random

log = getLogger(__name__)
AngelConfig = config.getConfig()
maxclones = AngelConfig.getint("common","maxclones")

class CloneLists(object):
    def __init__(self):
        self.good = []
        self.old = []
        self.unreachable = []

def accessible(clone):
    """
    Check if the clone is reachable, resolve redirects.
    @return a tuple of (Clone, bool), where Clone is the (redirected) clone, and bool indicates whether it's reachable.
    """
    if not clone.ping():
        log.debug("clone " + `clone` + " not reachable, ignoring")
        return (clone, False)
      
    clone = clone.checkForRedirect()
        
    if not clone.exists():
        log.debug("resource " + `clone.path` + " not found on host " + `clone.host`)
        return (clone, False)
    
    return (clone, True)

def acceptable(clone, publicKeyString, resourceID):
    """
    Compare the clone against the metadata, perform validation.
    
    @return a boolean, indicating if the clone is valid
    """
    
    if clone.resourceID() != resourceID:
        # an invalid clone
        log.debug("iterateClones: " + `clone` + " wrong resource ID")
        log.debug("expected: " + `resourceID`)
        log.debug("found: " + `clone.resourceID()`)
        return False
        
    if clone.publicKeyString() != publicKeyString:
        # an invalid clone
        log.debug("iterateClones: " + `clone` + " wrong public key")
        log.debug("expected: " + publicKeyString)
        log.debug("found: " + clone.publicKeyString())
        return False
        
    if not clone.validate():
        # an invalid clone
        log.debug("iterateClones: " + `clone` + " invalid signature")
        return False
    
    return True


def cloneList(cloneSeedList, publicKeyString, resourceID):
    """
    @return an iterable over _unique_ (clone, reachable) pairs
    
    @see accessible
    """
    
    validate = lambda clone: acceptable(clone, publicKeyString, resourceID)
    
    toVisit = copy.copy(cloneSeedList)
    visited = []
    
    while len(toVisit) != 0:
        
        # pop the next clone from the queue
        cc = toVisit[0]
        log.debug("inspecting clone: " + `cc`)
        toVisit = toVisit[1:]
    
        if cc in visited:
            # we have already looked at this clone -- don't bother with it
            log.debug("iterateClones: " + `cc` + " already visited, ignoring")
            continue

        try:
            (cc, acc) = accessible(cc)
        except CloneError, e:
            errorMessage = "Failure on clone inspection: " + `e` + " Ignoring: " + cc
            log.warn(errorMessage)
            # otherwise, mark the clone as checked and proceed (looking forward to the finally of python2.5)
            visited.append(cc)           
            continue

        # otherwise, mark the clone as checked and proceed
        visited.append(cc)
        
        if acc and not validate(cc):
            log.debug("ignoring bad clone: " + `cc`)
            continue
        
        toVisit += cc.cloneList()        
        yield (cc, acc)
    
    raise StopIteration


def cloneListPartitionReachable(cl = []):
    """
    Partition a list of (clone, reachable) pairs as produced by cloneList into a pair of two lists,
    the first consisting of those that are reachable, the second consisting of those that are unreachable.
    
    @see cloneList
    """
    reachable = []
    unreachable = []
    for (clone, reach) in cl:
        if reach:
            reachable.append(clone)
        else:
            unreachable.append(clone)
            
    return (reachable, unreachable)

def orderByRevision(cl):
    """
    Order a list of clones by their revision number. We do this by first sorting the list, then
    using groupBy to produce a list of lists, the latter containing clones with the same revision number.
    
    Note the following about itertools groupBy (from http://docs.python.org/lib/itertools-functions.html):
    
    The returned group is itself an iterator that shares the underlying iterable with groupby(). 
    Because the source is shared, when the groupby object is advanced, the previous group is no longer visible. 
    So, if that data is needed later, it should be stored as a list:

    groups = []
    uniquekeys = []
    for k, g in groupby(data, keyfunc):
        groups.append(list(g))      # Store group iterator as a list
        uniquekeys.append(k)
    
    @return a list of lists of clones, grouped by revision number
    """
    def rev(clone):
        return clone.revision()
    
    def cmpRev(cloneA, cloneB):
        return cmp(cloneA.revision(), cloneB.revision())
    
    # the clones, highest revision first
    cl = reversed(sorted(cl, cmpRev))
    
    groups = []
    for k, g in itertools.groupby(cl, rev):
        groups.append(list(g))      # Store group iterator as a list
        
    return groups
    
    
    

def iterateClones(cloneSeedList, publicKeyString, resourceID):
    """
    get all the clones of the (valid) clones we have already looked at
    which are not among any (including the invalid) of the clones we
    have already looked at, and validate those clones.
    
    @rtype ([Clone], [Clone])
    @return a tuple of ([the list of valid clones], [the list of checked clones])
    """  
    cl = CloneLists()
    
    notBadClones = cloneList(cloneSeedList, publicKeyString, resourceID)
    (goodClones, unreachableClones) = cloneListPartitionReachable(notBadClones)
    
    cl.unreachable = unreachableClones
    
    orderedGoodClones = [oc for oc in orderByRevision(goodClones)]
    if len(orderedGoodClones) > 0:
        # the good clones are the newest clones
        cl.good = [gc for gc in orderedGoodClones[0]]
    for gc in orderByRevision(goodClones)[1:]:
        # append the rest to the old clones
        cl.old.extend(gc)

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