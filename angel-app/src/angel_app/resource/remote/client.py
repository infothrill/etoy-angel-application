import os
import random
import copy

from angel_app import elements
from angel_app.config import config
from angel_app.log import getLogger
from angel_app.resource.local.basic import Basic
from angel_app.resource.remote.clone import clonesToElement
import angel_app.singlefiletransaction

log = getLogger(__name__)

# get config:
AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")
maxclones = AngelConfig.getint("common","maxclones")

def readResponseIntoFile(resource, referenceClone):
    t = angel_app.singlefiletransaction.SingleFileTransaction()
    bufsize = 8192 # 8 kB
    safe = t.open(resource.fp.path, 'wb')
    readstream = referenceClone.open()
    EOF = False
    while not EOF:
        data = readstream.read(bufsize)
        if len(data) == 0:
            EOF = True
        else:
            safe.write(data)
    t.commit() # TODO: only commit if the download worked!


def updateMetaData(resource, referenceClone):    
    # then update the metadata
    keysToBeUpdated = elements.signedKeys + [elements.MetaDataSignature]
    
    for key in keysToBeUpdated:
        pp = referenceClone.getProperty(key)
        resource.deadProperties().set(pp)

def syncContents(resource, referenceClone):
    """
    Synchronize the contents of the resource from the reference clone.
    """
    path = resource.fp.path
    

    if referenceClone.isCollection():
        # handle directory
        
        if resource.exists() and not resource.isCollection():
            os.remove(path)
        if not resource.exists():
            os.mkdir(path)
    
    else:
        # handle file
        readResponseIntoFile(resource, referenceClone)

    
def sync(resource, referenceClone):
    """
    Update the resource from the reference clone, by updating the contents,
    then the metadata, in that order.
    
    @return whether the update succeeded.
    """ 
    syncContents(resource, referenceClone)
    updateMetaData(resource, referenceClone)  
    

def ensureLocalValidity(resource, referenceClone):
    """
    Make sure that the local clone is valid and up-to-date, by synchronizing from a reference
    clone, if necessary.
    
    @param resource the local resource
    @param referenceClone a (valid, up-to-date) reference resource, which may be remote
    """

    old = referenceClone.revision() > resource.revision()
    
    if resource.exists() and resource.verify() and not old:
        # all is fine
        return

    sync(resource, referenceClone)
    
    assert resource.verify(), "Resource invalid after update."
    
    # even a valid resource may be unreferenced by the parent (i think TODO: check)    
    resource.garbageCollect()
    

def storeClones(af, goodClones, unreachableClones):
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
    gc = copy.copy(goodClones)
    random.shuffle(gc)
    
    uc = copy.copy(unreachableClones)
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
    
    cloneElements = clonesToElement(clonesToBeStored)
    af.deadProperties().set(cloneElements)


def broadCastAddress(localResource, destinations):
    """
    Broadcast availability of local clone to remote destinations.
    
    TODO: this needs more cowbell!
    """
    from angel_app.resource.remote import clone
    requestBody = clone.makeCloneBody(localResource)
    for clone in destinations:
        if not clone.ping(): continue
        if not clone.exists(): continue
        clone.remote.performRequest(method = "PROPPATCH", body = requestBody)

def inspectResource(af):

    goodClones, dummybadClones, unreachableClones = \
        iterateClones(
                      af.clones(), 
                      af.publicKeyString(), 
                      af.resourceID())
    
    if goodClones == []:
        log.info("no valid clones found for " + af.fp.path)
        return
    
    # the valid clones should all be identical, pick any one that exists for future reference
    rc = random.choice(goodClones)

    ensureLocalValidity(af, rc)
    storeClones(af, goodClones, unreachableClones)
    broadCastAddress(af, goodClones)
    
    


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
    good = []
    bad = []
    unreachable = []
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
            unreachable.append(cc)
            continue
        
        cc.checkForRedirect()
        
        if not cc.exists():
            log.debug("iterateClones: resource " + `cc.path` + " not found on host " + `cc`)
            bad.append(cc)
            continue
        
        if cc.resourceID() != resourceID:
            # an invalid clone
            log.debug("iterateClones: " + `cc` + " wrong resource ID")
            log.debug("expected: " + `resourceID`)
            log.debug("found: " + `cc.resourceID()`)
            bad.append(cc)
            continue
        
        if cc.publicKeyString() != publicKeyString:
            # an invalid clone
            log.debug("iterateClones: " + `cc` + " wrong public key")
            log.debug("expected: " + publicKeyString)
            log.debug("found: " + cc.publicKeyString())
            bad.append(cc)
            continue
        
        if not cc.validate():
            # an invalid clone
            log.debug("iterateClones: " + `cc` + " invalid signature")
            bad.append(cc)
            continue
        
        rr = cc.revision()
        
        if rr < revision:
            # too old
            log.debug("iterateClones: " + `cc` + " too old: " + `rr` + " < " + `revision`)
            if cc not in bad:
                bad.append(cc)
            continue
        
        if rr > revision:
            # hah! the clone is newer than anything
            # we've seen so far. all the clones we thought
            # were good are in fact bad.
            log.debug("iterateClones: " + `cc` + " very new: " + `rr` + " > " + `revision`)
            bad.extend(good)
            good = []
            revision = rr
        
        # we only arrive here if the clone is valid and sufficiently new
        good.append(cc)
        log.debug("iterateClones: adding good clone: " + `cc`)
        log.debug(`cc.cloneList()`)
        toVisit += cc.cloneList()
        
        

    log.info("iterateClones: good clones: " + `good`)
    log.info("iterateClones: bad clones: " + `bad`)
    
    return good, bad, unreachable
    