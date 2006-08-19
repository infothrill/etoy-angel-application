from twisted.python import log
from config.common import rootDir
from angel_app import elements
from angel_app.maintainer.util import relativePath
from angel_app.angelFile.basic import Basic

from angel_app.maintainer.clone import splitParse, Clone
from angel_app.maintainer.clone import iterateClones

DEBUG = True

def getLocalCloneURLList(af):
    """
    @param af -- an AngelFile
    """
    #print elements.Clones().toxml()
    
    try:
        clones = af.deadProperties().get(elements.Clones.qname())
    except:
        # we have no clones
        DEBUG and log.err(af.fp.path + ": no clones")
        return
    
    return [str(clone.children[0].children[0]) for clone in clones.children]

def getLocalCloneList(af):
    hostPorts = [splitParse(url) for url in getLocalCloneURLList(af)]
    return [Clone(url, port) for url, port in hostPorts]


def inspectResource(path = rootDir):
    #if DEBUG and relativePath(resource.path) != "": raise "debugging and stopping beyond root: " + relativePath(resource.path)
    DEBUG and log.err("inspecting resource: " + path)
    DEBUG and log.err("relative path is: " + relativePath(path))
    af = Basic(path)
    
    if not af.exists: return
    
    
    validClones, checkedClones = iterateClones(
                                               getLocalCloneList(af), 
                                               [],
                                               af.publicKeyString())
    DEBUG and log.err("DONE\n\n")
    