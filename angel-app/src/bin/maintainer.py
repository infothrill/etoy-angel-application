from optparse import OptionParser
from angel_app.log import getLogger

from angel_app.resource.remote import client, setup
from angel_app.graph import graphWalker
from twisted.python import log
from angel_app.resource.local.basic import Basic

setup.setupDefaultPeers()

from angel_app.config import config
AngelConfig = config.getConfig()
repository = AngelConfig.get("common", "repository")

def bootInit():
	"""
	Method to be called in __main__ before anything else. This method cannot rely on any
	framework being initialised, e.g. no logging, no exception catching etc.
	"""
	import angel_app.config.defaults
	angel_app.config.defaults.appname = "maintainer"
	
	
	# TODO: ugly twisted workaround to provide angel_app xml elements
	from twisted.web2.dav.element import parser
	from angel_app import elements
	parser.registerElements(elements)

def runServer():
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
            
if __name__ == "__main__":
    bootInit()
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-l", "--log", dest="networklogging", help="use network logging?", action="store_true" , default=False)
    (options, args) = parser.parse_args()

    import angel_app.log
    angel_app.log.setup()
    angel_app.log.enableHandler('file')
    if len(options.daemon) > 0:
        angel_app.log.enableHandler('socket')
        from angel_app import proc
        proc.startstop(action=options.daemon, stdout='maintainer.stdout', stderr='maintainer.stderr', pidfile='maintainer.pid')
    else:
        if (options.networklogging):
            angel_app.log.enableHandler('socket')
        else:
            angel_app.log.enableHandler('console')
    angel_app.log.getReady()
    DEBUG = True
    runServer()

