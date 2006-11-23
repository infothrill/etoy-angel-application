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
        exactly if the file is is not in a consistent state.
        See also proppatch.
        """             
        try:
            if not self.verify():
                raise responsecode.FORBIDDEN
        except:
            raise responsecode.FORBIDDEN
        
        return request
