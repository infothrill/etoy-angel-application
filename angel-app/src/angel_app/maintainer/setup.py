from angel_app.resource.local.basic import Basic
from angel_app import elements
from twisted.web2.dav.element.rfc2518 import HRef
from config.common import rootDir
from config import rootDefaults
import config.external

from angel_app.maintainer.util import syncClones
DEBUG = True

angelRoot = Basic(rootDir)

def cloneFromName(name = ("localhost", 90)):
    """
    Takes a node description in the form of a (hostname/ip-address, port number)
    tuple (the port number is optional) and generates a clone element from it.
    """
    hostname = name[0]
    if len(name) == 2: port = name[1]
    else: port = config.external.port
    
    return elements.Clone(
                          HRef.fromString(hostname + ":" + `port`))

def defaultPeers():
    """
    Generates an angel_app.elements.Clones element from the default_peers
    list.
    """
    return elements.Clones(
                    *[
                     cloneFromName(peer) 
                     for peer in rootDefaults.peers
                     ]
                    )


def setupDefaultPeers():
    """
    In the initial (i.e. during first installation) of the angel-app,
    we just need to make sure that the root directory contains a reference
    to one or more default peers. Once we have copied those over, the
    maintenance loop will do the rest.
    """
    syncClones(angelRoot, defaultPeers())