author = """Vincent Kraeutler 2007"""

from angel_app.config.config import getConfig
from angel_app.log import initializeLogging
from angel_app.maintainer import client
from angel_app.resource.remote.clone import Clone
import unittest
import os
from angel_app.resource.local.basic import Basic

getConfig().container['common']['loglevel'] = 'DEBUG' # global loglevel
try:
    del getConfig().container['logfilters']
except:
    pass

initializeLogging()

repositoryPath = getConfig().get("common","repository")
from angel_app.maintainer import mount

class CollectTest(unittest.TestCase):
    
    def testGetMountTab(self):
        """
        run through
        """
        mount.getMountTab()
    
    def testAddMounts(self):
        """
        run through
        """
        mount.addMounts()
        


        