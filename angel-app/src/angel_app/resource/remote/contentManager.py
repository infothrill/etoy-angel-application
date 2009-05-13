from angel_app.resource.IReadonlyContentManager import IReadonlyContentManager
from angel_app.resource.abstractContentManager import AbstractReadonlyContentManager
from twisted.web2 import responsecode
from zope.interface import implements

class ContentManager(AbstractReadonlyContentManager):

    implements(IReadonlyContentManager)
    
    def __init__(self, resource):
        self.resource = resource

    def openFile(self):
        response = self.resource.remote.performRequest()
        if response.status != responsecode.OK:
            raise "must receive an OK response for GET, otherwise something's wrong"
        return response
    
    def contentLength(self):
        # we're only interested in the header, so issue a HEAD request only
        rr = self.resource.performRequest(method = "HEAD")
        return long(rr.getheader("content-length"))
        