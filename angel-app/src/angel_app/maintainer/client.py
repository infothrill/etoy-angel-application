from angel_app import elements
from angel_app.config import config
from angel_app.graph import graphWalker
from angel_app.log import getLogger
from angel_app.maintainer import sync
from angel_app.maintainer import update
from angel_app.resource import childLink
from angel_app.resource.local.basic import Basic
from angel_app.resource.remote.clone import clonesToElement
from twisted.web2.dav import davxml
import angel_app.singlefiletransaction
import os
import random
import time

log = getLogger(__name__)
AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")


def inspectResource(af):
    """
    I take care of the inspection of a single resource, by first comparing it to all
    available valid clones, updating if necessary, and then broadcasting my existence
    to whoever is inclined to listen.
    """
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

       
def getChildren(resource):
    """
    TODO: this definitely needs more cowbell. Ideally, resources should provide
    something like a children() method, that returns a list of children.
    """
    childLinks = childLink.parseChildren(resource.childLinks())
    names = [cc.name for cc in childLinks]
    childPaths = [os.sep.join([resource.fp.path, nn]) for nn in names]
    for pp in childPaths:
        print "child:", pp
    childResources = [Basic(path) for path in childPaths]
    return childResources

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

