import time

from angel_app.config import config
from angel_app.graph import graphWalker
from angel_app.log import getLogger
from angel_app.maintainer import sync
from angel_app.maintainer import update
from angel_app.resource.local.basic import Basic

log = getLogger(__name__)
AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")


def inspectResource(af):
    """
    I take care of the inspection of a single resource, by first comparing it to all
    available valid clones, updating if necessary, and then broadcasting my existence
    to whoever is inclined to listen.
    """
    log.info("inspecting resource: " + af.fp.path)
    update.updateResource(af)
    sync.broadCastAddress(af)
    
def newSleepTime(currentSleepTime, startTime):
    """
    Determine new time to sleep between resource updates
    """
    maxSleepTime = AngelConfig.getint("maintainer", "maxsleeptime")
    traversalTime = AngelConfig.getint("maintainer", "treetraversaltime")
    
    elapsedTime = int(time.time()) - startTime
    if elapsedTime > traversalTime:
        sleepTime = currentSleepTime / 2
    else:
        sleepTime = currentSleepTime * 2 + 1
        if sleepTime > maxSleepTime:
            sleepTime = maxSleepTime
    return sleepTime

def isMountOfMount(resource):
    """
    We don't replicate other people's mount points (to avoid circular mounts).
    @return True if this resource is a mount point of a mount point, false otherwise.
    """
    if resource.isWritableFile() or resource.parent().isWritableFile():
        # either the resource or its parent belong to us. no mount of a mount
        return False
    elif resource.publicKeyString() == resource.parent().publicKeyString():
        return False

    return True
       
def getChildren(resource):
    """
    @return the children of the resource which are not indirectly mounted.
    """
    cleanChildren = [rr for rr in resource.children() if not isMountOfMount(rr)]
    return cleanChildren

def traverseResourceTree(sleepTime):
    """
    I do one traversal of the local resource tree.
    """
    def toEvaluate(resource, dummy = None):
        time.sleep(sleepTime)
        return (inspectResource(resource), None)
     
    for dummyii in graphWalker(Basic(repository), getChildren, toEvaluate):
        continue
    

def maintenanceLoop():
    """
    Main loop for the maintainer.
    """
    assert(Basic(repository).exists()), "Root directory (%s) not found." % repository

    sleepTime = AngelConfig.getint("maintainer", "initialsleep")
    while 1:
        log.info("sleep timeout between resource inspections is: " + `sleepTime`)
        startTime = int(time.time())

        # register with the tracker
        from angel_app.tracker.connectToTracker import connectToTracker
        dummystats = connectToTracker()
        traverseResourceTree(sleepTime)   
        sleepTime = newSleepTime(sleepTime, startTime)

