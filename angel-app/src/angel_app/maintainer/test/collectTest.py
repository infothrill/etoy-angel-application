author = """Vincent Kraeutler 2007"""

import unittest
from angel_app.resource.remote.clone import Clone
from angel_app.maintainer import collect

from angel_app.config.config import getConfig
getConfig().container['common']['loglevel'] = 'DEBUG' # global loglevel
del getConfig().container['logfilters'] # get rid of filters


from angel_app.log import initializeLogging
initializeLogging()


class CollectTest(unittest.TestCase):
    
    def testAccessible(self):
        clone = Clone("missioneternity.org")
        (cc, acc) = collect.accessible(clone)
        assert acc
        assert cc == clone
        
        clone2 = Clone("sample.invalid")
        (cc, acc) = collect.accessible(clone2)
        assert False == acc
        assert cc == clone2