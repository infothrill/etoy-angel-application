from twisted.python import log
from config.common import rootDir
from angel_app import elements
from angel_app.resource.remote.util import relativePath
from angel_app.resource.local.basic import Basic

from angel_app.resource.remote.clone import splitParse, Clone, iterateClones

DEBUG = True

def getLocalCloneURLList(af):
    """
    @param af -- an AngelFile
    """
    #print elements.Clones().toxml()
    clones = []
    
    try:
        clones += af.deadProperties().get(elements.Clones.qname()).children
    except:
        # we have no clones on this file
        pass

    try:
        clones += af.parent().deadProperties().get(elements.Clones.qname()).children
    except:
        # we have no clones on this file
        pass    
    
    return [str(clone.children[0].children[0]) for clone in clones]

def getLocalCloneList(af):
    """
    @return the local list of clones of the root directory.
    @rtype [Clone]
    """
    hostPorts = [splitParse(url) for url in getLocalCloneURLList(af)]
    return [Clone(url, port) for url, port in hostPorts]


def inspectResource(path = rootDir):
    log.err("bla")
    DEBUG and log.err("inspecting resource: " + path)
    DEBUG and log.err("relative path is: " + relativePath(path))
    af = Basic(path)
    
    if not af.exists: return
    
    DEBUG and log.err("reference data to be signed: " + af.signableMetadata() + af.getXml(elements.MetaDataSignature))
    DEBUG and af.verify()
    goodClones, badClones = iterateClones(getLocalCloneList(af), af.publicKeyString())
    
    if goodClones == []:
        log.err("no valid clones found for " + path)
        return
    
    log.err("inspectResource: valid clones: " + `goodClones`)
    
    # the valid clones should all be identical, pick any one for future reference
    rc = goodClones[0]
    
    log.err("reference clone: " + `rc`)
    
    # first, make sure the local clone is fine:
    # TODO: this is gunk.
    if rc.revision() > af.revisionNumber() or not af.verify() and af.fp.isdir():
        af.fp.open().write(rc.stream().read())
             
    
    # update all invalid clones with the meta data of the reference clone
    for bc in badClones: 
        DEBUG and log.err("updating invalid clone: " + bc.host)
        bc.performPushRequest(af)
        if af.exists() and not af.fp.isdir():
            bc.putFile(af.fp.open())
        
    
    
    
    DEBUG and log.err("DONE\n\n")
    