from twisted.python import log
from twisted.web2.dav.element import rfc2518
from angel_app import elements
from angel_app.resource.local.basic import Basic
from angel_app.resource.remote.clone import Clone
from urlparse import urlsplit

DEBUG = True

# get config:
from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")

def splitParse(cloneUri):
    host, rest = cloneUri.split(":")
    fragments = rest.split("/")
    port = int(fragments[0])
    
    if len(fragments) > 1:
        return host, port, "/" + "/".join(fragments[1:])
    
    return host, port

def cloneFromGunk(gunk):
    assert len(gunk) > 1
    assert len(gunk) < 4
    if len(gunk) == 2: return Clone(gunk[0], gunk[1])
    else: return Clone(gunk[0], gunk[1], gunk[2])


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
        pclones = af.parent().deadProperties().get(elements.Clones.qname()).children
        for pc in pclones: pc.path = af.relativePath()
        clones += pclones
    except:
        # we have no clones on this file
        pass    
    
    return [str(clone.children[0].children[0]) for clone in clones]

def getLocalCloneList(af):
    """
    @return the local list of clones of the root directory.
    @rtype [Clone]
    """
    return [cloneFromGunk(splitParse(url)) for url in getLocalCloneURLList(af)]

def _ensureLocalValidity(resource, referenceClone):
    """
    Make sure that the local clone is valid and up-to-date, by synchronizing from a reference
    clone, if necessary.
    
    @param resource the local resource
    @param referenceClone a (valid, up-to-date) reference resource, which may be remote
    """
    
    
    # first, make sure the local clone is fine:
    if referenceClone.isCollection():
        if not resource.exists():
            from twisted.web2.dav.fileop import mkcollection
            mkcollection(resource.fp)
    else:
        if (not resource.exists()) or (referenceClone.revision() > resource.revisionNumber()):

            open(resource.fp.path, "w").write(referenceClone.stream().read())
                    
            # update the file contents, if necessary
            DEBUG and log.err("_ensureLocalValidity: updating file contents for " + 
                              resource.fp.path + " " + `resource.exists()`
                              + " " + `referenceClone.revision()` + " " + `resource.revisionNumber()`
                              + " " + `resource.verify()`)

            
           
    if not resource.verify():
        # then update the metadata
        rp = referenceClone.propertiesDocument(elements.signedKeys)
        re = rp.root_element.childOfType(rfc2518.Response
                     ).childOfType(rfc2518.PropertyStatus
                   ).childOfType(rfc2518.PropertyContainer)
        
        for sk in elements.signedKeys:
            dd = re.childOfType(sk)
            resource.deadProperties().set(dd)
            
        DEBUG and log.err("_ensureLocalValidity, local clone's signed keys are now: " + resource.signableMetadata())   
        
    resource.familyPlanning()
    
    
            
def _updateBadClone(af, bc):  
            

    if bc.host == "localhost":
        # the local resource must be valid when we call this function, so no update necessary
        return
        
    if not bc.ping():
        # the remote clone is unreachable, ignore for now
        return
        
    DEBUG and log.err("updating invalid clone: " + `bc`)
        
    # push the resource
    if not af.isCollection():
        bc.putFile(open(af.fp.path))
    else:
        # it's a collection, which by definition does not have "contents",
        # instead, just make sure it exists:
        if not bc.exists():
            DEBUG and log.err("remote collection resource does not exist yet, creating collection")
            bc.mkCol()
            
    # push the resource metadata
    bc.performPushRequest(af)

def getResourceID(resource):
    """
    the resource ID delivered with the parent is actually more trustworthy, 
    because it has just been updated, however, the root directory has no parent....
    TODO: review
    """
    resourceID = ""
    if not resource.parent():
        # root directory
        resourceID = resource.resourceID()
    else:
        # otherwise, take the resourceID delivered from the parent
        # yumyum. python prose. enjoy.
        # TODO: our current xml metdatata model sucks rocks. possibly elementTree to the rescue?
        children = resource.parent().deadProperties().get(elements.Children.qname()).children
        for child in children:
            if str(child.childOfType(rfc2518.HRef.qname())) == resource.resourceName():
                xx = child.childOfType(elements.ResourceID.qname())
                log.err("ASDF" + `xx` + xx.toxml())
                resourceID = "".join(str(cc) for cc in child.childOfType(elements.ResourceID.qname()).children)
                log.err("ASDF" + resourceID)
        
    DEBUG and log.err("resourceID: " + `resourceID`)
    return resourceID

def inspectResource(path = repository):

    DEBUG and log.err("inspecting resource: " + path)
    af = Basic(path)
    
    # at this point, we have no guarantee that a local clone actually
    # exists. however, we do know that the parent exists, because it has
    # been inspected before


    standin = af.exists() and af or af.parent()
    pubKey = standin.publicKeyString()
    startingClones = getLocalCloneList(standin)
    resourceID = getResourceID(af)
    DEBUG and log.err("starting out iteration with: " + `startingClones`)
    goodClones, badClones = iterateClones(startingClones, pubKey, resourceID)
    
    if goodClones == []:
        DEBUG and log.err("no valid clones found for " + path)
        raise StopIteration
    
    DEBUG and log.err("inspectResource: valid clones: " + `goodClones`)
    
    # the valid clones should all be identical, pick any one for future reference
    rc = goodClones[0]
    
    DEBUG and log.err("reference clone: " + `rc` + " local path " + af.fp.path)

    _ensureLocalValidity(af, rc)
       
    af.deadProperties().set(
                            elements.Clones(*[
                                elements.Clone(rfc2518.HRef(`cc`)) for cc in goodClones
                                            ]))

    # update all invalid clones with the meta data of the reference clone
    for bc in badClones: 
        _updateBadClone(af, bc)
    
    
    DEBUG and log.err("DONE\n\n")
    
    


def iterateClones(cloneSeedList, publicKeyString, resourceID):
    """
    get all the clones of the (valid) clones we have already looked at
    which are not among any (including the invalid) of the clones we
    have already looked at, and validate those clones.
    
    @rtype ([Clone], [Clone])
    @return a tuple of ([the list of valid clones], [the list of checked clones])
    """  
    import copy
    toVisit = copy.copy(cloneSeedList)
    visited = []
    good = []
    bad = []
    ugly = []
    revision = 0
    
    while len(toVisit) != 0:
        # there are clones that we need to inspect
        
        # pop the next clone from the queue
        cc = toVisit[0]
        DEBUG and log.err("inspecting clone: " + `cc`)
        toVisit = toVisit[1:]
        
        if cc in visited:
            # we have already looked at this clone -- don't bother with it
            DEBUG and log.err("iterateClones: " + `cc` + " ignoring")
            continue
               
        # otherwise, mark the clone as checked and proceed
        visited.append(cc)
        
        if not cc.ping():
            DEBUG and log.err("iterateClones: clone " + `cc` + " no reachable, ignoring")
            continue
        
        if not cc.exists():
            DEBUG and log.err("iterateClones: resouce " + `cc.path` + " not found on host " + `cc`)
            bad.append(cc)
            continue
        
        if cc.resourceID() != resourceID:
            # an invalid clone
            DEBUG and log.err("iterateClones: " + `cc` + " wrong resource ID")
            DEBUG and log.err("expected: " + `resourceID`)
            DEBUG and log.err("found: " + `cc.resourceID()`)
            bad.append(cc)
            continue
        
        if cc.publicKeyString() != publicKeyString:
            # an invalid clone
            DEBUG and log.err("iterateClones: " + `cc` + " wrong public key")
            DEBUG and log.err("expected: " + publicKeyString)
            DEBUG and log.err("found: " + cc.publicKeyString())
            bad.append(cc)
            continue
        
        if not cc.validate():
            # an invalid clone
            DEBUG and log.err("iterateClones: " + `cc` + " invalid signature")
            bad.append(cc)
            continue
        
        rr = cc.revision()
        
        if rr < revision:
            # too old
            DEBUG and log.err("iterateClones: " + `cc` + " too old: " + `rr` + " < " + `revision`)
            if cc not in bad:
                bad.append(cc)
            continue
        
        if rr > revision:
            # hah! the clone is newer than anything
            # we've seen so far. all the clones we thought
            # were good are in fact bad.
            DEBUG and log.err("iterateClones: " + `cc` + " very new: " + `rr` + " > " + `revision`)
            bad.extend(good)
            good = []
            revision = rr
        
        # we only arrive here if the clone is valid and sufficiently new
        good.append(cc)
        DEBUG and log.err("iterateClones: adding good clone: " + `cc`)
        toVisit += [Clone(host, port) for host, port in cc.cloneList()]
        
        

    DEBUG and log.err("iterateClones: good clones: " + `good`)
    DEBUG and log.err("iterateClones: bad clones: " + `bad`)
    
    return good, bad
    