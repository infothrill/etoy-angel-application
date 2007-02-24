from optparse import OptionParser
from angel_app.log import getLogger
from angel_app.config import config
AngelConfig = config.getConfig()

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
    from angel_app.resource.remote import client, setup
    from angel_app.graph import graphWalker
    from angel_app.resource.local.basic import Basic

    repository = AngelConfig.get("common", "repository")
    getLogger().info("starting inspection loop at: " + repository)
    setup.setupDefaultPeers()

    def getChildren(path):
        children = [cc.fp.path for cc in Basic(path).metaDataChildren()]
        DEBUG and log.err("children of " + path + " are " + `children`)
        return children
    
    def toEvaluate(foo, bar):
    	return (client.inspectResource(foo), None)
    
    assert(Basic(repository).exists()), "Root directory (%s) not found." % repository
    
    while 1:
    	import time
    	for ii in graphWalker(repository, getChildren, toEvaluate):
    		sleeptime = AngelConfig.getint("maintainer", "sleep")
    		time.sleep(sleeptime)
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
        from angel_app import daemonizer
        daemonizer.startstop(action=options.daemon, stdout='maintainer.stdout', stderr='maintainer.stderr', pidfile='maintainer.pid')
    else:
        if (options.networklogging):
            angel_app.log.enableHandler('socket')
        else:
            angel_app.log.enableHandler('console')
    angel_app.log.getReady()
    DEBUG = True
    runServer()

