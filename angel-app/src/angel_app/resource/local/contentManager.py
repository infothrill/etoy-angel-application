from angel_app.resource.IReadonlyContentManager import IReadonlyContentManager
from angel_app.resource.abstractContentManager import AbstractReadonlyContentManager
from zope.interface import implements
from twisted.web2.dav.static import DAVFile

class ContentManager(AbstractReadonlyContentManager):

    implements(IReadonlyContentManager)
    
    def __init__(self, resource):
        self.resource = resource

    def openFile(self):
        return self.resource.fp.open()
        
    def contentLength(self):
        return super(DAVFile, self.resource).contentLength()
        