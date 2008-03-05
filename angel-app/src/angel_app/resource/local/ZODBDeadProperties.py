from zope.interface import implements
from angel_app.resource.IDeadPropertyStore import IDeadPropertyStore

class ZODBDeadProperties(object):
    """
    """
    implements(IDeadPropertyStore)
    
    def __init__(self):
        pass
    
        """
    Provide a zope interface specification of property stores as found in twisted.web2.dav
    """
    def get(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """

    def set(self, property):
        """
        @param property -- an instance of twisted.web2.dav.davxml.WebDAVElement
        """
        
    def delete(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """

    def contains(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """

    def list(self):
        """
        """