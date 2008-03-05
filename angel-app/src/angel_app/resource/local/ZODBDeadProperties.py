from zope.interface import implements
from angel_app.resource.IDeadPropertyStore import IDeadPropertyStore
from ZEO.ClientStorage import ClientStorage

class ZODBDeadProperties(object):
    """
    """
    implements(IDeadPropertyStore)
    
    def __init__(self, _resource):
        self.resource = _resource
        addr = "localhost", 6223
        self.connection = ClientStorage(addr)

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