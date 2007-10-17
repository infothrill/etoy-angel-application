def bootInit():
    """
    Method to be called in __main__ before anything else. This method cannot rely on any
    framework being initialised, e.g. no logging, no exception catching etc.
    """    
    pass

def postConfigInit():
    """
    Run this method after the config system is initialized.
    """
    from angel_app.admin.directories import makeDirectories
    makeDirectories()

    # setup our internal temporary path for files:
    from angel_app import singlefiletransaction
    singlefiletransaction.setup()

def dance(options):
    from angel_app.log import getLogger
    from angel_app.resource.remote import client
    from angel_app.graph import graphWalker
    from angel_app.resource.local.basic import Basic
    from angel_app.config import config

    log = getLogger("maintainer")
    AngelConfig = config.getConfig()
    repository = AngelConfig.get("common", "repository")
    log.info("starting inspection loop at: " + repository)

    def getChildren(resource):
        return [child for (child, path) in resource.findChildren("1")]
    
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

        # register with the tracker
        from angel_app.tracker.connectToTracker import connectToTracker
        dummystats = connectToTracker()
    
        time.sleep(sleepTime)
        for dummyii in graphWalker(Basic(repository), getChildren, toEvaluate):
            time.sleep(sleepTime)
            continue
        
        elapsedTime = int(time.time()) - startTime
        if elapsedTime > traversalTime:
            sleepTime = sleepTime / 2
        else:
            sleepTime = sleepTime * 2 + 1
            if sleepTime > maxSleepTime:
                sleepTime = maxSleepTime


def boot():
    bootInit()
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
    parser.add_option("-l", "--log", dest="networklogging", help="use network logging?", action="store_true" , default=False)
    (options, dummyargs) = parser.parse_args()

    # setup/configure config system
    from angel_app.config.config import getConfig
    angelConfig = getConfig(options.config)
    postConfigInit()
    angelConfig.bootstrapping = False

    appname = "maintainer"
    # setup/configure logging
    from angel_app.log import initializeLogging
    loghandlers = ['file'] # always log to file
    if len(options.daemon) > 0:
        loghandlers.append('socket')
    else:
        if (options.networklogging):
            loghandlers.append('socket')
        else:
            loghandlers.append('console')
    initializeLogging(appname, loghandlers)

    if len(options.daemon) > 0:
        from angel_app.proc import daemonizer
        daemonizer.startstop(action=options.daemon, stdout=appname+'.stdout', stderr=appname+'.stderr', pidfile=appname+'.pid')

    return options
                

if __name__ == '__main__':
    options = boot()
    dance(options)