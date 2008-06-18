"""
Routines for updating a local resource from _all_ accessible remote clones.
"""

from angel_app.log import getLogger
from angel_app.maintainer import collect
from angel_app.maintainer import sync
from angel_app.resource.remote.clone import clonesToElement
from angel_app.resource import childLink

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
    except KeyboardInterrupt:
        raise
    except Exception:
        # in that case, our current resource is most certainly outdated...
        # TODO: throws an HTTPError, which is certainly inappropriate..
        old = True
    
    if resource.exists() and resource.verify() and not old:
        # all is fine
        return True
    else:
        sync.updateLocal(resource, referenceClone)
        return resource.verify()

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
            log.info("Failed to update local resource from clone: " + clone.toURI(),  exc_info = e)
    assert False, "Failed to update local resource %s from clone list." % resource.fp.path
        

def storeClones(af, goodClones, unreachableClones):
    """
    @param af: the local resource
    @param goodClones: good clones of this resource
    @param unreachableClones: unreachableClones of this resource
    
    @see:  iterateClones
    """
    
    clonesToStore = collect.clonesToStore(goodClones, unreachableClones)
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
    Either return the resource's clones directly (if they exist), or inherit them from the parent.
    """
    if af.exists():
        return af.clones()
    else:
        from angel_app.resource.local.propertyManager import inheritClones
        return inheritClones(af)
    
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
    for (child, path) in storedChildren:
        if not linkedChildren.has_key(child.resourceName()):
            log.info("unlinking: " + `child`)
            child.remove()
    

def updateResource(af):
    """
    Inspect the resource, updating it if necessary.
    """
    cloneLists = collect.iterateClones(
                      discoverSeedClones(af), 
                      discoverPublicKey(af), 
                      discoverResourceID(af))
    
    if cloneLists.good == []:
        log.info("no valid clones found for " + af.fp.path)
    else:
        updateResourceFromClones(af, cloneLists.good)

    if af.exists():        
        storeClones(af, cloneLists.good, cloneLists.old + cloneLists.unreachable)
        removeUnreferencedChildren(af)
        if af.validate():
            return True
        else:
            log.warn("Resource was not valid after update: " + af.fp.path)
            return False
    else:
        log.warn("update did not create local resource for " + af.fp.path)
        return False
