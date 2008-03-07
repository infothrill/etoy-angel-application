from ZEO.ClientStorage import ClientStorage
from angel_app.config.config import getConfig
from angel_app.resource.IDeadPropertyStore import IDeadPropertyStore
from zope.interface import implements
from ZODB import DB
import transaction

def getZEOAddress():
    return (
        "127.0.0.1", 
        getConfig().getint("zeo","listenPort")
        )
    
zodbRoot = DB(
   ClientStorage(
                 getZEOAddress()
                 )).open().root()

class ZODBDeadProperties(object):
    """
    """
    implements(IDeadPropertyStore)
    
    def __init__(self, _resource):
        self.resource = _resource

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