"""
Routines for updating a local resource from _all_ accessible remote clones.
"""

from itertools import chain

from angel_app.log import getLogger
from angel_app.maintainer import collect
from angel_app.maintainer import sync
from angel_app.resource.remote.clone import clonesToElement
from angel_app.resource import childLink
from angel_app.resource.remote.exceptions import CloneError

log = getLogger(__name__)

def updateResourceFromClone(resource, referenceClone):
    """
    Make sure that the local clone is valid and up-to-date, by synchronizing from a reference
    clone, if necessary.
    
    @param resource the local resource
    @param referenceClone a (valid, up-to-date) reference resource, which may be remote
    
    @return True, if the resource is valid after update, False otherwise
    """

    try:
        # this will fail, if the resource does not (yet) actually exist on the file system
        old = referenceClone.revision() > resource.revision()
        if old:
            log.debug("local %r is older than reference clone %r: %s < %s", resource, referenceClone, resource.revision(), referenceClone.revision())
    except KeyboardInterrupt:
        raise
    except Exception:
        # in that case, our current resource is most certainly outdated...
        # TODO: throws an HTTPError, which is certainly inappropriate..
        old = True
    
    if resource.exists() and resource.validate() and not old:
        # all is fine
        return True
    else:
        sync.updateLocal(resource, referenceClone)
        return resource.validate()

def updateResourceFromClones(resource, cloneList):
    """
    Step through a list of clones, synchronizing the local resource, until the resource is valid.
    """
    for clone in cloneList:
        try:
            if updateResourceFromClone(resource, clone):
                return
        except KeyboardInterrupt:
            raise
        except Exception, e:
            log.info("Failed to update local resource from clone: %s", clone.toURI(),  exc_info = e)
    assert False, "Failed to update local resource %s from clone list." % resource.fp.path
        

def storeClones(af, goodClones, unreachableClones):
    """
    @param af: the local resource
    @param goodClones: good clones of this resource
    @param unreachableClones: unreachableClones of this resource
    
    @see:  iterateClones
    """
    clonesToStore = collect.clonesToStore(goodClones, unreachableClones)
    if len(clonesToStore) == 0:
        log.warn("no clones to store. cowardly refusing to create an empty clonelist")
        return
    cloneElements = clonesToElement(clonesToStore)
    af.deadProperties().set(cloneElements)
    

def discoverResourceID(af):
    """
    Either return the resource's id directly (if it exists), or extract it from 
    the parent's child links.
    """
    if af.exists():
        return af.resourceID()
    else:
        # obtain the resource id from the parent's child link
        childLinks = childLink.parseChildren(af.parent().childLinks())
        for cl in childLinks:
            if af.resourceName() == cl.name:
                return cl.id
        raise KeyError, "Resource " + af.fp.path + " not found in parent's links: " + af.parent().childLinks()

def discoverSeedClones(af):
    """
    Either return the resource's clones directly (if they exist), or inherit
    them from the parent.
    
    @return: tuple (seedClones, inheritedClones)
    """
    seedclones = []
    if af.exists():
        seedclones = af.clones()

    # We are not allowed to assume that getting the clone list from a local
    # clone results in a good, usable clonelist, so we always try to avoid having
    # an empty clone list by always inheriting clones additionally.
    from angel_app.resource.local.propertyManager import inheritClones
    return (seedclones, inheritClones(af))
    
def discoverPublicKey(af):
    if af.exists():
        return af.publicKeyString()
    else:
        from angel_app.resource.local.propertyManager import getOnePublicKey
        return getOnePublicKey(af)

def removeUnreferencedChildren(resource):
    """
    Remove all child resources that on the file system that are not listed in the
    parent's child list. To be called for _existing_ resources _after_ a completed
    update.
    """
    # the resources linked in the metadata
    linkedChildren = dict([(cc.resourceName(), cc) for cc in resource.children()]) 
    # the child resources found on the file system
    storedChildren = resource.findChildren("1") 
    for (child, dummypath) in storedChildren:
        if not linkedChildren.has_key(child.resourceName()):
            log.info("unlinking: %r", child)
            child.remove()
    

def discoverBroadCastClones(lclone, cloneList):
    """
    Find all remote clones in cloneList that do not know about lclone.
    
    @param lclone: clone
    @param cloneList: list of clones
    """
    broadcastClones = []
    for c in cloneList:
        try:
            if lclone not in c.cloneList():
                broadcastClones.append(c)
        except CloneError, e:
            # ignore IO and network issues, just collect what we can find
            log.debug("got a clone error while discovering broadcast clones: %r", e)
    return collect.eliminateDNSDoubles(collect.eliminateSelfReferences(broadcastClones))

def updateResource(lresource):
    """
    Inspect the resource, updating it if necessary.
    Returns a tuple containing (isValid, newGoodClones)
    """
    (thisClones, inheritedClones) = discoverSeedClones(lresource) 
    cloneLists = collect.iterateClones(
                      lresource,
                      thisClones + inheritedClones,
                      discoverPublicKey(lresource), 
                      discoverResourceID(lresource))
   
    # When we have no local clones yet, we will have to download the complete
    # remote clone to validate it, which sucks in terms of speed.
    # Then, when we have downloaded all clones, we proceed below by redownloading
    # it again in order to create/update the local clone.
    # TODO: optimize!!!
    if cloneLists.good == []:
        log.info("no good clones found for %s", lresource.fp.path)
    else:
        updateResourceFromClones(lresource, cloneLists.good)

    if lresource.exists():
        storeClones(lresource, cloneLists.good, cloneLists.old + cloneLists.unreachable)
        removeUnreferencedChildren(lresource)
        if lresource.validate():
            # Gather the clones to which we want to announce this local resource
            # by taking good, old and bad clones and announcing ourselves to them
            # if they don't know about us yet:
            log.debug("lresource is valid: %s, collecting clones for broadcast...", lresource)
            broadcastClones = discoverBroadCastClones(lresource.makeClone(), chain(cloneLists.good, cloneLists.old, cloneLists.bad))
            return (True, broadcastClones)
        else:
            log.warn("Resource was not valid after update: %s", lresource.fp.path)
            return (False, [])
    else:
        log.warn("update did not create local resource for %s", lresource.fp.path)
        return (False, [])
