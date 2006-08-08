from twisted.python import log
from config.common import rootDir
from angel_app import elements
from angel_app.maintainer.util import relativePath
from angel_app.angelFile.basic import Basic

from angel_app.maintainer.clone import splitParse, Clone


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

def getLocalCloneList(cloneURLList):
    clones = []
    for url in cloneURLList:
        hostname, port = splitParse(url)
        clones.append(Clone(hostname, port))
    return clones

def inspectResource(path = rootDir):
    #if DEBUG and relativePath(resource.path) != "": raise "debugging and stopping beyond root: " + relativePath(resource.path)
    DEBUG and log.err("inspecting resource: " + path)
    DEBUG and log.err("relative path is: " + relativePath(path))
    af = Basic(path)
    updateClones(af)
    DEBUG and log.err("DONE\n\n")
    