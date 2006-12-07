from angel_app.maintainer.client import inspectResource
from angel_app.maintainer.setup import setupDefaultPeers
from angel_app.graph import graphWalker
from twisted.python import log
from angel_app.resource.local.basic import Basic

setupDefaultPeers()

from config.common import rootDir

            
if __name__ == "__main__":
    log.err("starting inspection loop")
    
    def getChildren(path):
        return [cc.fp.path for cc in Basic(path).metaDataChildren()]
    
    def toEvaluate(foo, bar):
        return (inspectResource(foo), None)
    
    for ii in graphWalker(rootDir, getChildren, toEvaluate):
        continue
    #walkTree()