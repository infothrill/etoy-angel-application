"""
Routines for synchronizing a local clone with a _single_ remote peer.
"""
import os
import time

from angel_app import elements
from angel_app.log import getLogger
from angel_app.singlefiletransaction import SingleFileTransaction
from angel_app.io import RateLimit
from angel_app.io import bufferedReadLoop
from angel_app.config.config import getConfig

cfg = getConfig()
MAX_DOWNLOAD_SPEED = cfg.getint('common', 'maxdownloadspeed_kib') * 1024 # internally handled in bytes
log = getLogger(__name__)

def syncContents(resource, referenceClone):
    """
    Synchronize the contents of the resource from the reference clone.
    """
    path = resource.fp.path
    
    if referenceClone.isCollection():
        # handle directory        
        if resource.exists() and not resource.isCollection():
            os.remove(path)
        if not resource.exists():
            os.mkdir(path)   
    else:
        # handle file
        readResponseIntoFile(resource, referenceClone)
        

def readResponseIntoFile(resource, referenceClone):
    t = SingleFileTransaction()
    safe = t.open(resource.fp.path, 'wb')
    stream = referenceClone.open()
    size = long(stream.getheader('Content-Length'))
    callbacks = [ safe.write, RateLimit(size, MAX_DOWNLOAD_SPEED) ]
    try:
        numbytesread = bufferedReadLoop(stream.read, 4096, size, callbacks)
        assert numbytesread == size, "Download size does not match expected size"
    except Exception, e:
        log.warn("Error while downloading clone '%s'" % str(referenceClone), exc_info = e)
        t.cleanup()
        raise
    else:
        t.commit()
    

def updateMetaData(resource, referenceClone):    
    # then update the metadata
    keysToBeUpdated = elements.signedKeys + [elements.MetaDataSignature]
    
    for key in keysToBeUpdated:
        pp = referenceClone.getProperty(key)
        resource.deadProperties().set(pp)
        
    
def updateLocal(resource, referenceClone):
    """
    Update the resource from the reference clone, by updating the contents,
    then the metadata, in that order.
    
    @return whether the update succeeded.
    """ 
    syncContents(resource, referenceClone)
    updateMetaData(resource, referenceClone)  
    

def _parallelBroadcast(localResource, clones):
    """
    this will broadcast to all clones in parallel. Internally forks() and thus
    might not work in some situations (e.g. GUI thread)
    @param localResource: the local resource
    @param clones: the clones to be patched
    """
    class _LocalResourceBroadCaster(object):
        """
        Class to be used as a callable callback for broadcasting the local
        resource to the given remote clone. (Could also be done with a closure)
        """
        def __init__(self, localResource):
            self.res = localResource
        def __call__(self, clone):
            clone.announce(self.res) # should never fail, as defined!
            return 0

    broadcaster = _LocalResourceBroadCaster(localResource)
    from angel_app.contrib.delegate import parallelize
    
    parallelize(broadcaster, clones, children=6) # max 6 forks() at a time

def _sequentialBroadcast(localResource, clones):
    """
    this will broadcast to all clones in sequential order.
    @param localResource: the local resource
    @param clones: the clones to be patched
    """
    for clone in clones:
        clone.announce(localResource) # will not fail, as defined!

def broadCastAddress(localResource):
    """
    Broadcast availability of local clone to remote destinations.

    This method does not optimize in any way and broadcasts to all known
    clones of the local resource (no inheritance of clones!).
    """
    return broadCastAddressToClones(localResource, localResource.clones())
    
def broadCastAddressToClones(localResource, targetClones):
    """
    Broadcast availability of local clone to remote destinations.
    """
    if not cfg.getboolean('provider', 'enable'):
        return # pointless to broadcast if we don't serve the data

    if len(targetClones) < 1:
        return # no one to broadcast to
    
    t1 = time.time()
    _parallelBroadcast(localResource, targetClones)
    log.debug("speed: broadcast took %s sec", str(time.time() - t1))
