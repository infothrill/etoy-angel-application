from angel_app.resource.local.basic import Basic
from angel_app import elements
from twisted.web2.dav.element.rfc2518 import HRef
from angel_app.config import defaults
from angel_app.resource.remote.util import syncClones
from angel_app.log import getLogger

log = getLogger("setup")
DEBUG = True
DEBUG and log.debug("setup module loaded")

# get config:
from angel_app.config import config
AngelConfig = config.getConfig()
repository = Basic(AngelConfig.get("common","repository"))

def cloneFromName(name = ("localhost", 90)):
    """
    Takes a node description in the form of a (hostname/ip-address, port number)
    tuple (the port number is optional) and generates a clone element from it.
    """
    hostname = name[0]
    if len(name) == 2: port = name[1]
    else: port = config.defaults.publiclistenport # note: not using config file, but hardcoded default external port
    
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
                     for peer in defaults.peers
                     ]
                    )


def setupDefaultPeers():
    """
    In the initial (i.e. during first installation) of the angel-app,
    we just need to make sure that the root directory contains a reference
    to one or more default peers. Once we have copied those over, the
    maintenance loop will do the rest.
    """
    DEBUG and log.debug("running setupDefaultPeers")
    syncClones(repository, defaultPeers())