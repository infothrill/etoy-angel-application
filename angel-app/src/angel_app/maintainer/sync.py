"""
Routines for synchronizing a local clone with a _single_ remote peer.
"""
import os

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
    


def broadCastAddress(localResource):
    """
    Broadcast availability of local clone to remote destinations.
    """
    for clone in localResource.clones():
        try:
            # no ping() / exists(), as announce() may fail anyway
            clone.announce(localResource)
        except KeyboardInterrupt:
            raise
        except Exception, e:
            log.warn(
                     "Address broadcast failed for clone " + clone.toURI() \
                     + " of resource: " + localResource.fp.path, exc_info = e)