author = """Vincent Kraeutler 2007"""

from angel_app.config.config import getConfig
from angel_app.log import initializeLogging
from angel_app.maintainer import collect
from angel_app.resource.remote.clone import Clone
import unittest

getConfig().container['common']['loglevel'] = 'DEBUG' # global loglevel
#del getConfig().container['logfilters'] # get rid of filters

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
        
    def testAcceptable(self):
        """
        Validating a (reachable) clone against itself should always succeed.
        """
        clone = Clone("missioneternity.org")
        assert collect.acceptable(clone, 
                                  clone.publicKeyString(), 
                                  clone.resourceID())
        
    def testCloneList(self):
        clone = Clone("missioneternity.org")
        cl = [cc for cc in collect.cloneList([clone], 
                                             clone.publicKeyString(), 
                                             clone.resourceID()
                                             )]
        print cl
        assert len(cl) > 0
        
    def testIterateClones(self):
        clone = Clone("missioneternity.org")
        cl = collect.iterateClones([clone], 
                                    clone.publicKeyString(), 
                                    clone.resourceID()
                                    )
        
        if len(cl.good) > 0:
            ref = cl.good[0]
            for cc in cl.good[1:]:
                assert cc.revision() == ref.revision()
                assert cc.publicKeyString() == clone.publicKeyString()
                assert cc.resourceID() == clone.resourceID()
                assert cc.validate()
            
        for cc in cl.old:
            assert cc not in cl.good
            assert cc not in cl.unreachable
            assert cc.validate()
            if len(cl.good) > 0:
                assert cc.revision() < cl.good[0].revision()
                
        for cc in cl.unreachable:
            assert (not cc.ping()) or (not cc.exists())

        