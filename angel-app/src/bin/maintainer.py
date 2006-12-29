from angel_app.resource.remote import client, setup
from angel_app.graph import graphWalker
from twisted.python import log
from angel_app.resource.local.basic import Basic

setup.setupDefaultPeers()

from angel_app.config.common import rootDir

            
if __name__ == "__main__":
    log.err("starting inspection loop at: " + rootDir)
    
    def getChildren(path):
        return [cc.fp.path for cc in Basic(path).metaDataChildren()]
    
    def toEvaluate(foo, bar):
        try:
            return (client.inspectResource(foo), None)
        except:
            log.err("Inspection loop failed for resource: " + `foo`)
            raise StopIteration
    
    assert(Basic(rootDir).exists()), "Root directory (%s) not found." % rootDir
    
    for ii in graphWalker(rootDir, getChildren, toEvaluate):
        continue