"""
Routines for obtaining a best guess about the current replication state of a clone. 
"""

import itertools
import random
import socket

from angel_app.config import config
from angel_app.log import getLogger
from angel_app.resource.remote.exceptions import CloneError
import copy

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
        log.debug("clone %r not reachable, ignoring", clone)
        return (clone, False)

    clone = clone.checkForRedirect()
        
    if not clone.exists():
        log.debug("resource %r not found on host %r", clone.path, clone.host)
        return (clone, False)
    
    return (clone, True)

def acceptable(clone, publicKeyString, resourceID):
    """
    Compare the clone against the metadata, perform complete validation.
    
    @return a boolean, indicating if the clone is valid
    """
    try:
        if clone.resourceID() != resourceID:
            # an invalid clone
            return False
        
        if clone.publicKeyString() != publicKeyString:
            # an invalid clone
            return False
        
        if not clone.validate():
            # an invalid clone
            log.debug("iterateClones: %r invalid signature", clone)
            return False
    
        return True
    except KeyboardInterrupt:
        raise
    except Exception, e:
        log.info("Clone %s not acceptable().", clone.toURI(), exc_info = e)
        return False

def acceptableChunk(lresource, clone, publicKeyString, resourceID):
    """
    Compare the clone against the metadata, perform validation based on byte ranges.
    
    @return a boolean, indicating if the clone is valid
    """
    CHUNKLENGTH = 4096 # the number of bytes to be validated

    try:
        if clone.resourceID() != resourceID:
            # an invalid clone
            return False
        
        if clone.publicKeyString() != publicKeyString:
            # an invalid clone
            return False
        
        # here we do a comparison of a chunk of data only
        size = lresource.contentLength()
        startoffset = random.randint(0, size)
        if startoffset + CHUNKLENGTH > size:
            CHUNKLENGTH = size - startoffset 
            log.debug("had to shrink the chunk to verify to %s bytes. Offset: %s, resource-size: %s", CHUNKLENGTH, startoffset, size)
        log.debug("doing byte range based validation of a resource of size %s, saving %s bytes traffic", size, size - CHUNKLENGTH)
        localdigest = lresource.getChunkHash(startoffset, CHUNKLENGTH)
        remotedigest = clone.getChunkHash(startoffset, CHUNKLENGTH)
        assert localdigest is not None
        assert remotedigest is not None, "Remote clone unreachable?"
        if localdigest == remotedigest:
            return True
        else:
            log.info("remote clone %r is not acceptable", clone)
            return False
    except Exception, e:
        log.info("Clone %s not acceptable().", clone.toURI(), exc_info = e)
        return False

class ValidateClone(object):
    """
    A class to be used as a filter on a list of clones of which we need to
    figure out wether the members are acceptable for 
     a- syncing to a non-existant/broken local resource
     b- keeping them as a meta property in the clonelist
    """
    def __init__(self, lresource, publicKeyString = None, resourceID = None):
        self.lresource = lresource
        self.publicKeyString = publicKeyString
        self.resourceID = resourceID
        if publicKeyString is None:
            self.publicKeyString = lresource.publicKeyString()
        if resourceID is None:
            self.resourceID = lresource.resourceID()
        self._doByteRangeValidation = self._canDoByteRangeValidationWith(lresource)

    def _canDoByteRangeValidationWith(self, lresource):
        try: # don't make inspection fail on broken local resources because we
            # want to optimize for the good case where the local resource is valid!
            if not lresource.isCollection():
                if lresource.validate():
                    #log.debug("_canDoByteRangeValidationWith(): True " + `lresource`)
                    return True
        except:
            pass
        #log.debug("_canDoByteRangeValidationWith(): False " + `lresource`)
        return False
    
    def __call__(self, clone):
        # the clone should be reachable at this point!
        # check if it's good:
        # log.debug("__call__ in ValidateClone for " + `clone`)
        if self._doByteRangeValidation:
            return acceptableChunk(self.lresource, clone, self.publicKeyString, self.resourceID)
        else:
            return acceptable(clone, self.publicKeyString, self.resourceID)

def cloneList(lresource, cloneSeedList, publicKeyString, resourceID):
    """
    @return an iterable over _unique_ (clone, reachable) pairs
    
    @see accessible
    """
    
    #validate = lambda clone: acceptable(clone, publicKeyString, resourceID)
    validate = ValidateClone(lresource, publicKeyString, resourceID)

    toVisit = copy.copy(cloneSeedList)
    visited = []
    
    while len(toVisit) != 0:
        
        # pop the next clone from the queue
        cc = toVisit[0]
        toVisit = toVisit[1:]
        
        log.debug("visiting: %r", cc)
    
        if cc in visited:
            # we have already looked at this clone -- don't bother with it
            log.debug("ignoring already visited clone: %r", cc)
            continue

        # mark this clone as visited        
        visited.append(cc) 

        # here, we may receive a redirect, which may of course be broken and fail
        try:
            (cc, acc) = accessible(cc)
        except CloneError, e:
            log.warn("Failure on clone inspection: %r (Invalid redirect?) Ignoring: %r", e, cc)          
            continue

        # if a redirect happened, mark also the new clone as visited
        if cc not in visited:
            visited.append(cc)
        
        # the clone is reachable -- check if it's good.
        if acc and (not validate(cc)):
            log.debug("ignoring bad clone: %r", cc)
            continue
        
        if acc:
            log.debug("accepting good clone: %r and extending clone list.", cc)
            # clone is reachable and good -- look also at its clones:
            toVisit += cc.cloneList()
        else:
            log.debug("keeping unreachable clone (it might be good eventually): %r",  cc)        
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
    
    
    

def iterateClones(lresource, cloneSeedList, publicKeyString, resourceID):
    """
    get all the clones of the (valid) clones we have already looked at
    which are not among any (including the invalid) of the clones we
    have already looked at, and validate those clones.
    
    @rtype ([Clone], [Clone])
    @return a tuple of ([the list of valid clones], [the list of checked clones])
    """  
    cl = CloneLists()
    
    notBadClones = cloneList(lresource, cloneSeedList, publicKeyString, resourceID)
    (goodClones, unreachableClones) = cloneListPartitionReachable(notBadClones)
    
    cl.unreachable = unreachableClones
    
    orderedGoodClones = [oc for oc in orderByRevision(goodClones)]
    if len(orderedGoodClones) > 0:
        # the good clones are the newest clones
        cl.good = [gc for gc in orderedGoodClones[0]]
    for gc in orderByRevision(goodClones)[1:]:
        # append the rest to the old clones
        cl.old.extend(gc)

    log.info("good clones: %r", cl.good)

    return cl
    
def anyin(totest, reference):
    """
    Tests wether any of the elements in iterable 'totest' is in container 'reference'.
    @param totest: any iterable
    @param reference: container type (e.g. implements __contains__)
    """
    for element in totest:
        if element in reference: return True
    return False

def eliminateSelfReferences(clones):
    """
    Takes a list of clones and filters out clones that seemingly refer to
    the local node. This is done by comparing the clone.host with a list
    of hardcoded names and a the IP addresses that the nodename refers to 
    """
    selfNodeName = AngelConfig.get("maintainer","nodename")
    selfReferences = ["localhost", "127.0.0.1", "::1", selfNodeName]
    try:
        selfReferences.extend( [res[4][0] for res in socket.getaddrinfo(selfNodeName, None)] )
    except Exception: # allow DNS lookup to fail
        pass
    return [cc for cc in clones if cc.host not in selfReferences and not anyin(resolve(cc.host), selfReferences)]

def resolve(hostname):
    """
    helper method to resolve a hostname and return a list of IPs or the empty
    list

    @param hostname: hostname
    """
    try:
        return [ res[4][0] for res in socket.getaddrinfo(hostname, None) ]
    except Exception:
        pass
    return []

def eliminateDNSDoubles(clones):
    """
    awkward internet. Here we _try_ to filter out clone doubles that refer to
    the same node on the network by
     a- getting rid of clones with IP addresses for which we have a hostname
     b- resolving all hostnames and see if they point to the same IPs
    
    Note: this should work fine with multiple dns records (round robin). untested.

    @param clones: list of clones
    """
    def isNumericAddress(address):
        "Test if address is a numeric ip address"
        for family in [ socket.AF_INET, socket.AF_INET6 ]:
            try:
                socket.inet_pton(family, address)
                return True
            except socket.error:
                pass
        return False
    
    if len(clones) <= 1:
        return clones

    allhostnames = [c.getHost() for c in clones if not isNumericAddress(c.getHost())]
    resolved_ips = []
    for hostname in allhostnames:
        resolved_ips.extend( resolve(hostname) )

    result = []
    seen = []
    for cc in clones:
        if cc.getHost() not in resolved_ips:
            ips = resolve(cc.getHost())
            if len(ips) > 0:
                foo = [ ip for ip in ips if ip not in seen ]                
                if len(foo) > 0:
                    seen.extend(ips)
                    result.append(cc)
            else:
                seen.extend(cc.getHost())
                result.append(cc)
    numeliminated = len(clones) - len(result)
    if numeliminated > 0:
        log.debug("eliminated %d clone(s) w.r.t. DNS/IP", numeliminated)
    return result


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
    gc = copy.copy(eliminateDNSDoubles(eliminateSelfReferences(goodClones)))
    random.shuffle(gc)
    
    uc = copy.copy(eliminateDNSDoubles(eliminateSelfReferences(unreachableClones)))
    random.shuffle(uc)
    
    clonesWeMightStore = gc + uc

    # fill in only non-duplicates    
    clonesToBeStored = []    
    for clone in clonesWeMightStore:
        # take only non-duplicates
        if clone not in clonesToBeStored:
            clonesToBeStored.append(clone)
            
        # guard against DOS and metadata overflow
        if len(clonesToBeStored) >= maxclones: break

    return clonesToBeStored