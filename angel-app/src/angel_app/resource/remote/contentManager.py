from angel_app import elements
from angel_app.resource.IReadonlyContentManager import IReadonlyContentManager
from angel_app.resource.abstractContentManager import AbstractReadonlyContentManager
from twisted.web2 import responsecode
from twisted.web2.dav import davxml
from twisted.web2.dav.element import rfc2518
from zope.interface import implements

class ContentManager(AbstractReadonlyContentManager):

    implements(IReadonlyContentManager)
    
    def __init__(self, remote):
        self.remote = remote

    def openFile(self):
        response = self.remote.performRequest()
        if response.status != responsecode.OK:
            raise "must receive an OK response for GET, otherwise something's wrong"
        return response.stream
    
    def contentLength(self):
        # TODO: defaults to GET request, but we're only interested in the header...
        rr = self.remote.performRequest() 
        clh = rr.getheader("content-length")
        cl = int(clh)
        return cl
        