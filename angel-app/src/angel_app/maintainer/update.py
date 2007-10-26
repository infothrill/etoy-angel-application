"""
Routines for updating a local resource from _all_ accessible remote clones.
"""

from angel_app.log import getLogger
from angel_app.maintainer import collect
from angel_app.resource.remote.clone import clonesToElement

log = getLogger(__name__)

def updateResourceFromClone(resource, referenceClone):
    """
    Make sure that the local clone is valid and up-to-date, by synchronizing from a reference
    clone, if necessary.
    
    @param resource the local resource
    @param referenceClone a (valid, up-to-date) reference resource, which may be remote
    
    @return True, if the resource is valid after update, False otherwise
    """

    old = referenceClone.revision() > resource.revision()
    
    if resource.exists() and resource.verify() and not old:
        # all is fine
        return True
    else:
        sync.updateLocal(resource, referenceClone)
        return resource.verify()

def updateResourceFromClones(resource, cloneList):
    """
    Step through a list of clones, syncrhonizing the local resource, until the resource is valid.
    """
    for clone in cloneList:
        if updateResourceFromClone(resource, clone):
            return
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
    

def updateResource(af):
    """
    Inspect the resource, updating it if necessary.
    """
    goodClones, dummybadClones, unreachableClones = \
        collect.iterateClones(
                      af.clones(), 
                      af.publicKeyString(), 
                      af.resourceID())
    
    if goodClones == []:
        log.info("no valid clones found for " + af.fp.path)
        return
    
    updateResourceFromClones(af, goodClones)
    storeClones(af, goodClones, unreachableClones)