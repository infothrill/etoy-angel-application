from angel_app.resource.local.basic import Basic
from angel_app.resource.local.external.methods import proppatch

from angel_app.log import getLogger
log = getLogger(__name__)

class External(proppatch.ProppatchMixin, Basic):
    """
    An AngelFile, as seen on the external (unsafe) network interface.
    """
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        Basic.__init__(self, path, defaultType, indexNames)
    
    def isWriteable(self):
        """
        A basic AngelFile is writeable (by a non-local host) exactly if:
          -- the resource is corrupted, i.e. it does not verify()
          -- the resource does not exist but is referenced by its parent()
          
        @rtype boolean
        @return whether the basic AngelFile is writeable
        """

        if not self.exists(): 
            pp = self.parent()
            if pp.verify() and self.referenced(): 
                log.debug(self.fp.path + " is writable")
                return True
        
        elif not self.verify():
            log.debug(self.fp.path + " is writable")
            return True
        

        
        log.debug(self.fp.path + " is not writable")
        return False