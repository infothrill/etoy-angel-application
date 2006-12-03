from twisted.web2.dav.static import DAVFile
from twisted.python import log
from twisted.web2 import responsecode, dirlist
from twisted.web2.http import HTTPError
from twisted.web2 import http, stream
from twisted.web2.dav.xattrprops import xattrPropertyStore
from angel_app import elements
from angel_app.angelFile.basic import Basic
from angel_app.davMethods.proppatch import ProppatchMixin

DEBUG = False

class External(ProppatchMixin, Basic):
    """
    An AngelFile, as seen on the external (unsafe) network interface.
    """
    
    def __init__(self, path,
                 defaultType="text/plain",
                 indexNames=None):
        Basic.__init__(self, path, defaultType, indexNames)

    def precondition_PUT(self, request):
        """
        A put operation from a non-authenticated source is allowed
        exactly if 
        -- the file does not exist, but is referenced in the parent resource
        -- the file is is not in a consistent state.
        See also proppatch.
        """ 
        
        if not self.exists() and not self in self.parent().metaDataChildren():
            raise HTTPError(
                    StatusResponse(
                       responsecode.FORBIDDEN, 
                       "PUT is forbidden on inexinstant unreferenced resources. Try a PROPPATCH first."
                       ))
                    
        if self.verify():
                raise HTTPError(
                    StatusResponse(
                           responsecode.FORBIDDEN, 
                           "PUT is forbidden on valid resources. Try a PROPPATCH first."
                           ))
        
        # permission granted
        return request
