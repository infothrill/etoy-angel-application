from twisted.python import log
from angel_app.config.common import rootDir
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
    absPath = af.fp.path
    DEBUG and log.err("inspecting resource: " + absPath)
    rp = relativePath(absPath)
    DEBUG and log.err("relative path is: " + rp)
    return [Clone(url, port, rp) for url, port in hostPorts]


def inspectResource(path = rootDir):

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
    if (rc.revision() > af.revisionNumber() or not af.verify()) and not af.fp.isdir():
        open(af.fp.path, "w").write(rc.stream().read())
             
    
    # update all invalid clones with the meta data of the reference clone
    for bc in badClones: 
        # at this point, the parent's meta data should already be up-to-date
        DEBUG and log.err("updating invalid clone: " + `bc`)
        
        # push the resource
        if not af.isCollection():
            bc.putFile(open(af.fp.path))
        else:
            if not bc.exists():
                log.err("resource does not exist yet, creating collection")
                bc.mkCol()
            
        log.err("resource exists, updating metadata")
        # push the resource metadata
        bc.performPushRequest(af)
    
    
    DEBUG and log.err("DONE\n\n")
    