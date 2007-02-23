from twisted.web2.dav.static import DAVFile
from twisted.python import log
from twisted.web2 import responsecode, dirlist
from twisted.web2.http import HTTPError
from twisted.web2 import http, stream
from twisted.web2.dav.xattrprops import xattrPropertyStore
from angel_app import elements

DEBUG = False

class TransactionalMixin:
    """
    Utilities for weak-ass transaction support. A transaction on all resources is guaranteed to proceed 
    atomically, exactly if all other destructive updates to the resource are also transactions. 
    """
    
    def acquireLock(self, numAttempts = 0, timeOut = 1):
        if self.locked():
            if numAttempts >= maxAttempts:
                raise "failed to acuire lock after many many attempts"
            
            reactor.callLater(self.acquireLock, numAttempts + 1, 2 * timeOut)
            
        self.lockToken = self.lock()
        
    def releaseLock(self):
        self.unlock(self.lockToken)
        
    
    def transaction(self, maybeDeferred):
        self.acquireLock()
        maybeDeferred.addCallback(self.releaseLock())