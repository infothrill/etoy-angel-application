from ZEO.ClientStorage import ClientStorage
from angel_app.config.config import getConfig
from angel_app.resource.IDeadPropertyStore import IDeadPropertyStore
from zope.interface import implements

def getZEOAddress():
    return (
        "127.0.0.1", 
        getConfig().getint("zeo","listenPort")
        )

class ZODBDeadProperties(object):
    """
    """
    implements(IDeadPropertyStore)
    
    def __init__(self, _resource):
        self.resource = _resource
        self.connection = ClientStorage(getZEOAddress())

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