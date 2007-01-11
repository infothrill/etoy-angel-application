from angel_app.resource.remote import client, setup
from angel_app.graph import graphWalker
from twisted.python import log
from angel_app.resource.local.basic import Basic

setup.setupDefaultPeers()

from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common","repository")

    
# TODO: ugly twisted workaround to provide angel_app xml elements
from twisted.web2.dav.element import parser
from angel_app import elements
parser.registerElements(elements)

DEBUG = True
            
if __name__ == "__main__":
    log.err("starting inspection loop at: " + repository)
    
    def getChildren(path):
        children = [cc.fp.path for cc in Basic(path).metaDataChildren()]
        DEBUG and log.err("children of " + path + " are " + `children`)
        return children
    
    def toEvaluate(foo, bar):
        #try:
            return (client.inspectResource(foo), None)
        #except:
        #    log.err("Inspection loop failed for resource: " + `foo`)
        #    raise StopIteration
    
    assert(Basic(repository).exists()), "Root directory (%s) not found." % repository
    
    for ii in graphWalker(repository, getChildren, toEvaluate):
        continue