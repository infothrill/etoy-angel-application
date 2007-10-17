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

def boot():
    from optparse import OptionParser
    bootInit()
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
    parser.add_option("-l", "--log", dest="networklogging", help="use network logging?",action="store_true" ,default=False)
    (options, dummyargs) = parser.parse_args()

    # setup/configure config system
    from angel_app.config.config import getConfig
    angelConfig = getConfig(options.config)
    postConfigInit()
    angelConfig.bootstrapping = False

    appname = "presenter"
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


def dance(options):
    from angel_app.log import getLogger
    from angel_app.config import config
    AngelConfig = config.getConfig()
    port = AngelConfig.getint("presenter","listenPort")
    interface = AngelConfig.get("presenter","listenInterface")
    repository = AngelConfig.get("common","repository")

    from angel_app.resource.local.internal.resource import Crypto
    Crypto.rootDirectory = repository
    root = Crypto(repository)

    from twisted.web2 import server
    from twisted.web2 import channel
    from twisted.internet import reactor
    site = server.Site(root)
    reactor.listenTCP(port, channel.HTTPFactory(site), 50, interface)
    getLogger().info('Listening on IP %s port %d and serving content from %s', interface, port, repository)
    reactor.run()

    
if __name__ == '__main__':
    options = boot()
    dance(options)