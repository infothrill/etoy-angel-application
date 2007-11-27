author = """Vincent Kraeutler 2007"""

from angel_app.config.config import getConfig
from angel_app.log import initializeLogging
from angel_app.maintainer import client
from angel_app.resource.remote.clone import Clone
import unittest
import os
from angel_app.resource.local.basic import Basic

getConfig().container['common']['loglevel'] = 'DEBUG' # global loglevel
#del getConfig().container['logfilters'] # get rid of filters

initializeLogging()

repositoryPath = getConfig().get("common","repository")

class CollectTest(unittest.TestCase):
    
    def testIsMountOfMount(self):
        """
        This test will fail, unless you're vincent.
        """
        polPath = os.sep.join([repositoryPath, "pol"])
        polResource = Basic(polPath)
        assert False == client.isMountOfMount(polResource)
        polM221ePath = os.sep.join([polPath, "MISSION ETERNITY"])
        polM221eResource = Basic(polM221ePath)
        print "writability: ", polM221eResource.isWritableFile()
        print "parent writability: ", polM221eResource.parent().isWritableFile()
        print "public key string: ", polM221eResource.publicKeyString()
        print "parent public key string: ", polM221eResource.parent().publicKeyString()
        assert True == client.isMountOfMount(polM221eResource)
        print polResource.children()

        