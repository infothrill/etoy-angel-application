author = """Vincent Kraeutler 2007"""

import unittest
from angel_app.resource.remote.clone import Clone
from angel_app.maintainer import collect

class CollectTest(unittest.TestCase):
    
    def testAccessible(self):
        clone = Clone("missioneternity.org")
        (cc, acc) = collect.accessible(clone)
        assert acc
        assert cc == clone
        
        clone2 = Clone("afadsf.net")
        (cc, acc) = collect.accessible(clone2)
        assert False == acc
        assert cc == clone2