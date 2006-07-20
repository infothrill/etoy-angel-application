from twisted.python.filepath import FilePath
from twisted.python import log

from angel_app.static import AngelFile
from angel_app import elements
from twisted.web2.dav.element.rfc2518 import HRef
from config.common import rootDir
from config.default_peers import default_peers
import config.external

DEBUG = True

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
                     for peer in default_peers
                     ]
                    )


def setupDefaultPeers():
    """
    In the initial (i.e. during first installation) of the angel-app,
    we just need to make sure that the root directory contains a reference
    to one or more default peers. Once we have copied those over, the
    maintenance loop will do the rest.
    """
    angelRoot = AngelFile(rootDir)
    dp = angelRoot.deadProperties()
    try:
        clones = dp.get(elements.Clones.qname())
    except:
        log.err("root directory has no clones -- initializing.")
        clones = elements.Clones()
    
    cc = [child for child in clones.children]
    for peer in defaultPeers().children:
        if peer not in cc:
            cc.append(peer)
    dp.set(elements.Clones(*cc))
    DEBUG and log.err(`dp.get(elements.Clones.qname())`)
    