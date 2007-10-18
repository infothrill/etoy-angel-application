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
        return self.resource.fp.open()
        
    def contentLength(self):
        return super(DAVFile, self.resource).contentLength()
        