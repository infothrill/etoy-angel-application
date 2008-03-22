from ZEO.ClientStorage import ClientStorage
from angel_app.config.config import getConfig
from angel_app.resource.IDeadPropertyStore import IDeadPropertyStore
from zope.interface import implements
from ZODB import DB
import transaction
from persistent.mapping import PersistentMapping
from persistent import Persistent

def getZEOAddress():
    return (
        "127.0.0.1", 
        getConfig().getint("zeo","listenPort")
        )

def getZODBRoot():
    """
    @return a new ZODB root instance -- opens a new connection
    """    
    return DB(
              ClientStorage(
                 getZEOAddress()
                 )).open().root()
                 

# lazily initialized ZODB root singleton:
defaultZODBRoot = []
                 
def getZODBDefaultRoot():
    """
    @return a root object from a shared connection.
    """
    if [] == defaultZODBRoot:
        defaultZODBRoot.append(getZODBRoot())
    return defaultZODBRoot[0]

repositoryRootPrefix = "repository"

def lookup(_zodb, _resource):
    """
    Look up a resource's metadata entry. Empty entries will be created
    for all nodes in the resources path if they don't exist yet.
    
    @param _zodb : a zodb root
    @param _resource : an angel_app.Basic resource
    """
    
    def walk(_zz, _rr, _modified = False):
        if [] == _rr:
            # we're done traversing
            if _modified:
                # we added entries during our traversal, a good time to commit.
                transaction.commit()
            return _zz
        
        # add resource if not already present
        res = _rr[0]
        if res not in _zz.children:
            _zz.children[res] = PersistentPropertyNode()
            return walk(_zz.children[res], _rr[1:], True)
        else:    
            return walk(_zz.children[res], _rr[1:])
    
    # create the root node for the repository, if necessary
    if repositoryRootPrefix not in _zodb:
        _zodb[repositoryRootPrefix] = PersistentPropertyNode()
        transaction.commit()  
            
    return walk(_zodb[repositoryRootPrefix], _resource.relativePathEntries())

class PersistentPropertyNode(Persistent):
    """
    A persistent object that contains "properties" (a persistent mapping from strings to strings)
    and "children" (a persistent mapping from strings to PersistentPropertyNodes)
    """
    def __init__(self):
        self.children = PersistentMapping()
        self.properties = PersistentMapping()
     
    
class ZODBDeadProperties(object):
    """
    """
    implements(IDeadPropertyStore)
    
    def __init__(self, _resource):
        self.resource = _resource
        self.zodb = lookup(getZODBDefaultRoot(), self.resource).properties
        
    def get(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """
        return self.zodb[qname]

    def set(self, property):
        """
        @param property -- an instance of twisted.web2.dav.davxml.WebDAVElement
        """
        self.zodb[property.qname()] = property
        transaction.commit()
        
    def delete(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """
        del self.zodb[qname]
        transaction.commit()

    def contains(self, qname):
        """
        @param qname (see twisted.web2.dav.davxml) of the property to look for.
        """
        return qname in self.zodb

    def list(self):
        """
        """
        return self.zodb.keys()
        