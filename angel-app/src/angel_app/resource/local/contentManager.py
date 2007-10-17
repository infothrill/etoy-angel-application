from angel_app import elements
from angel_app.resource.IReadonlyContentManager import IReadonlyContentManager
from angel_app.resource.abstractContentManager import AbstractReadonlyContentManager
from twisted.web2 import responsecode
from twisted.web2.dav import davxml
from twisted.web2.dav.element import rfc2518
from zope.interface import implements

class ContentManager(AbstractReadonlyContentManager):

    implements(IReadonlyContentManager)
    
    def __init__(self, resource):
        self.resource = resource

    def openFile(self):
        try:
            f = self.fp.open()
        except IOError, e:
            import errno
            if e[0] == errno.EACCES:
                raise HTTPError(responsecode.FORBIDDEN)
            elif e[0] == errno.ENOENT:
                raise HTTPError(responsecode.NOT_FOUND)
            else:
                raise
        return f
    
    def contentLength(self):
        # TODO: defaults to GET request, but we're only interested in the header...
        rr = self.remote.performRequest() 
        clh = rr.getheader("content-length")
        cl = int(clh)
        return cl
        