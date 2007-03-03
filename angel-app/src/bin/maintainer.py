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

def postConfigInit():
    """
    Run this method after the config system is initialized.
    """
    from angel_app.admin.directories import makeDirectories
    makeDirectories()

    # setup our internal temporary path for files:
    from angel_app import singlefiletransaction
    singlefiletransaction.setup()

def runServer():
    from angel_app.resource.remote import client, setup
    from angel_app.graph import graphWalker
    from angel_app.resource.local.basic import Basic

    log = getLogger("maintainer")
   
    repository = AngelConfig.get("common", "repository")
    log.info("starting inspection loop at: " + repository)
    setup.setupDefaultPeers()

    def getChildren(path):
        children = [cc.fp.path for cc in Basic(path).metaDataChildren()]
        DEBUG and log.debug("children of " + path + " are " + `children`)
        return children
    
    def toEvaluate(foo, bar):
        return (client.inspectResource(foo), None)
    
    assert(Basic(repository).exists()), "Root directory (%s) not found." % repository

    import time   
    sleepTime = AngelConfig.getint("maintainer", "initialsleep")
    traversalTime = AngelConfig.getint("maintainer", "treetraversaltime")
    maxSleepTime = AngelConfig.getint("maintainer", "maxsleeptime")
    while 1:
        log.info("sleep timeout between resource inspections is: " + `sleepTime`)
        startTime = int(time.time())
        try:

	        for ii in graphWalker(repository, getChildren, toEvaluate):
	             time.sleep(sleepTime)
	             continue
                             

                
        except:
            log.warn("an error occured while traversing the tree -- restarting")
        
        elapsedTime = int(time.time()) - startTime
        if elapsedTime > traversalTime:
            sleepTime = sleepTime / 2
        else:
            sleepTime = sleepTime * 2 + 1
            if sleepTime > maxSleepTime:
                sleepTime = maxSleepTime

        
            
if __name__ == "__main__":
    bootInit()
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
    parser.add_option("-l", "--log", dest="networklogging", help="use network logging?", action="store_true" , default=False)
    (options, args) = parser.parse_args()

    # setup/configure config system
    from angel_app.config.config import getConfig
    angelConfig = getConfig(options.config)
    angelConfig.bootstrapping = False
    postConfigInit()

    # setup/configure logging
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
