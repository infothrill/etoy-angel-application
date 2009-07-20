"""
Routines for obtaining a best guess about the current replication state of a clone. 
"""

import itertools
import random
import socket

#from angel_app.contrib.delegate import parallelize
from angel_app.worker import dowork
from angel_app.config import config
from angel_app.log import getLogger
#from angel_app.resource.remote.exceptions import CloneError

log = getLogger(__name__)
AngelConfig = config.getConfig()
maxclones = AngelConfig.getint("common","maxclones")

class CloneLists(object):
    """
    A python style struct
    """
    def __init__(self):
        self.good = []
        self.old = [] # valid but out-dated
        self.unreachable = []
        self.bad = [] # reachable but broken

    def __str__(self):
        return "good: %r, old: %r, unreachable: %r, bad: %r" % (self.good, self.old, self.unreachable, self.bad)

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
        # TODO: more specific exception catching
        log.info("Clone %s not acceptable().", clone.toURI(), exc_info = e)
        return False

def canDoByteRangeValidationWith(lresource):
    """
    test wether the given local resource can be used to optimize validation
    of remote clones (e.g. byte range based validation). For this, the resource
    must be valid and not a container type resource.
    @param lresource: local resource
    """
    try: # don't make inspection fail on broken local resources because we
        # want to optimize for the good case where the local resource is valid!
        if not lresource.isCollection():
            if lresource.validate():
                #log.debug("_canDoByteRangeValidationWith(): True " + `lresource`)
                return True
    except Exception, e:
        log.debug("TODO: more specific exception handling", exc_info = e)
    #log.debug("_canDoByteRangeValidationWith(): False " + `lresource`)
    return False

class ValidateClone(object):
    """
    A class to be used as a callback to filter a list of clones of which we
    need to figure out wether the members are acceptable for:
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
        self._doByteRangeValidation = canDoByteRangeValidationWith(lresource)
    
    def __call__(self, clone):
        # the clone should be reachable at this point!
        # check if it's good:
        # log.debug("__call__ in ValidateClone for " + `clone`)
        if self._doByteRangeValidation:
            return acceptableChunk(self.lresource, clone, self.publicKeyString, self.resourceID)
        else:
            return acceptable(clone, self.publicKeyString, self.resourceID)

def basicCloneChecks(toVisit, accessibleCb, validateCb):
    """
    This method is a helper to run some checks on a list of clones and return
    the results.
    
    @param toVisit: list of clones to check
    @param accessibleCb: callback to check accessibility / redirects etc.
    @param validateCb: callback to check if clone is valid
    
    @return: dictionary with clone as key, and dictionaries with keys 'accessible' and 'valid'
    """
    resultMap = {}
    if len(toVisit) < 1: return resultMap
    accessibleResult = dowork(accessibleCb, toVisit)  # TODO: CloneError
    log.debug("accessibility check done")
    #log.debug("%r", accessibleResult)
    for tt in accessibleResult.itervalues(): # mark redirects as seen
        if type(tt) != type(tuple()): # TODO: exceptions in parallelization
            log.warn("FOO %r", exc_info = tt)
        if tt[0] not in resultMap:
            resultMap[tt[0]] = { 'accessible': tt[1], 'valid': False } # valid: default to false
    toValidate = [ t[0] for t in accessibleResult.itervalues() if t[1] == True ]
    if len(toValidate) > 0:
        validationResult = dowork(validateCb, toValidate)
        log.debug("validation done")
        for cc in validationResult.keys():
            if validationResult[cc]: # valid!
                resultMap[cc]['valid'] =  True
    return resultMap

    
def clonesFor(lresource, cloneSeedList, publicKeyString, resourceID):
    """
    This method will take the local resource, combined with a list of seed clones,
    its public key string, its id and then:
      (1) check the validity of the seed clones (reachability+validity)
      (2) discover unknown/new clones and run (1)
      (3) yield unique clones for the local resource
    The yielded clones might be accessible, unreachable, valid, invalid,
    previously known, newly discovered etc.
    
    yields tuples of: (clone, accessible, valid)
    
    @param lresource:
    @param cloneSeedList:
    @param publicKeyString:
    @param resourceID:
    """
    # create validation callback:
    validate = ValidateClone(lresource, publicKeyString, resourceID)
    # before visiting clones, get rid of duplicate junk:
    toVisit = eliminateDNSDoubles(eliminateSelfReferences(cloneSeedList))

    visited = []

    def getCloneList(clone):
        return clone.cloneList()

    while len(toVisit) > 0:
        resultMap = basicCloneChecks(toVisit, accessible, validate)
        toVisit = []
        for cc in resultMap:
            visited.append(cc)
            yield( (cc, resultMap[cc]['accessible'], resultMap[cc]['valid']) )
        # discover new clones based on valid clones:
        validClones = [ cc for cc in resultMap if resultMap[cc]['valid'] ]
        if len(validClones) > 0:
            for ctocheck in eliminateDNSDoubles(eliminateSelfReferences(itertools.chain(*dowork(getCloneList, validClones).itervalues()))):
                if ctocheck not in visited and ctocheck not in toVisit:
                    log.debug("discovered new clone: %r", ctocheck)
                    toVisit.append(ctocheck)
    raise StopIteration
    

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
    okClones = [] # might be old
    for (c, reachable, valid) in clonesFor(lresource, cloneSeedList, publicKeyString, resourceID):
        if not reachable: cl.unreachable.append(c)
        elif valid: okClones.append(c)
        else: cl.bad.append(c)

    # take okClones and sort by revision:
    orderedGoodClones = [oc for oc in orderByRevision(okClones)]
    if len(orderedGoodClones) > 0:
        # the good clones are the newest clones
        cl.good = [gc for gc in orderedGoodClones[0]]
    for gc in orderByRevision(okClones)[1:]:
        # append the rest to the old clones
        cl.old.extend(gc)

    log.debug("clonesFor(%s): %s", lresource, cl)

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
    selfReferences.extend( resolvedns(selfNodeName) )
    return [cc for cc in clones if cc.host not in selfReferences and not anyin(resolvedns(cc.host), selfReferences)]

def resolvedns(hostname):
    """
    helper method to resolve a hostname and return a list of IPs or the empty
    list

    @param hostname: hostname
    """
    try:
        return [ res[4][0] for res in socket.getaddrinfo(hostname, None) ]
    except socket.error:
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
        resolved_ips.extend( resolvedns(hostname) )

    result = []
    seen = []
    for cc in clones:
        if cc.getHost() not in resolved_ips:
            ips = resolvedns(cc.getHost())
            if len(ips) > 0:
                newips = [ ip for ip in ips if ip not in seen ]                
                if len(newips) > 0:
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
    #gc = copy.copy(eliminateDNSDoubles(eliminateSelfReferences(goodClones))) # pk: why copy?
    gc = eliminateDNSDoubles(eliminateSelfReferences(goodClones))
    random.shuffle(gc)
    
    #uc = copy.copy(eliminateDNSDoubles(eliminateSelfReferences(unreachableClones))) # pk: why copy?
    uc = eliminateDNSDoubles(eliminateSelfReferences(unreachableClones))
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