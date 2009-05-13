import os
import time
import random

from __future__ import division # to make those sleepTime calculations real

from angel_app.config import config
from angel_app.graph import graphWalker
from angel_app.log import getLogger
from angel_app.maintainer import sync
from angel_app.maintainer import update
from angel_app.resource import childLink
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
    try:
        update.updateResource(af)
        sync.broadCastAddress(af)
        return True
    except KeyboardInterrupt:
        raise
    except Exception, e:
        log.error("Resource inspection failed for resource: " + af.fp.path, exc_info = e)
        return False
    
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
        sleepTime = currentSleepTime * 2 + random.random() # random() returns 0<x<1
        if sleepTime > maxSleepTime:
            sleepTime = maxSleepTime
    return sleepTime
       
def getChildren(resource):
    """
    @return the children of the resource which are not indirectly mounted.
    """
    if resource.isWritableFile():
        # either the resource belongs to us. no mount of a mount, none of the 
        # children are mounts of mounts, simply return all children
        return resource.children()
    else:
        # return only those children for which the key UUID is equal to
        # the current resource's key UUID
        parentUuid = resource.keyUUID()
        childLinks = childLink.parseChildren(resource.childLinks())
        return [Basic(os.sep.join([resource.fp.path, cl.name])) for cl in childLinks if cl.uuid == parentUuid]

def traverseResourceTree(sleepTime):
    """
    I do one traversal of the local resource tree.
    """
    def timedValidation(resource, dummy = None):
        log.info("sleeping for %d sec" %sleepTime)
        time.sleep(sleepTime)
        return (inspectResource(resource), None)
    
    log.growl("User", "MAINTENANCE PROCESS", "Starting resource tree traversal.")
     
    for dummyii in graphWalker(Basic(repository), getChildren, timedValidation):
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
        
        # check all mount points
        from angel_app.maintainer import mount
        mount.addMounts()
        
        traverseResourceTree(sleepTime)   
        sleepTime = newSleepTime(sleepTime, startTime)

