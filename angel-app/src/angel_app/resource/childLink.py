from angel_app import elements
from angel_app.contrib import uuid
from twisted.web2.dav import davxml
import urllib

class ChildLink(object):
    
    def __init__(self):
        pass
    
    def fromChildElement(self, childElement):
        assert isinstance(childElement, elements.Child)
        
        url = childElement.childOfType(davxml.HRef)
        self.name = urllib.unquote(str(url))
        
        self.id = childElement.childOfType(elements.ResourceID)
        self.uuid = uuid.UUID(str(childElement.childOfType(elements.UUID)))
        
        return self
    

def parseChildren(childrenElement):
    assert isinstance(childrenElement, elements.Children)
    
    return [
            ChildLink().fromChildElement(cc)
            for cc in childrenElement.children
            ]