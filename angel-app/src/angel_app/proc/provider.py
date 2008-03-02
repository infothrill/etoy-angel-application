import sys

# dyndns: initial test. Should probably go somewhere else than this module
import angel_app.contrib.dyndnsc as dyndnsc

def getDynDnsConfiguration(angelConfig):
    """
    fetches dyndns configuration from angel config, if unconfigured or wrongly configured,
    returns None.
    
    This method serves as a bridge, so we can re-use dyndnsc.getDynDnsClientForConfig().

    @param angelConfig: an AngelConfig instance
    @return: a dictionary with key value pair options
    """
    from angel_app.log import getLogger
    required_keys = {'protocol': 'dyndns', 'hostname': None }
    other_keys = {'key': None, 'userid': None, 'password': None, 'sleeptime': 60, 'method': 'webcheck'}
    for key in required_keys.keys():
        try:
            option = angelConfig.get('dyndns', key)
        except:
            # if a required key is missing, return None to disable dyndns explicitly
            getLogger().warn("dyndns config incomplete: missing key '%s'" % key)
            return None
        else:
            required_keys[key] = option
    for key in other_keys.keys():
        try:
            option = angelConfig.get('dyndns', key)
        except:
            # if an optional key is missing, ignore and use our default
            pass
        else:
            other_keys[key] = option

    # merge require and optional keys into one dictionary:
    for key in other_keys.keys():
        required_keys[key] = other_keys[key]
    return required_keys


def getCallLaterDynDnsClientForAngelConfig(angelConfig, callLaterMethod, logger):
    """
    factory method to instantiate and initialize a complete and working dyndns client for 
    use in the reactor loop.
    
    @param config: a dictionary with configuration pairs
    @return: None or a valid object for use with reactor.callLater()  
    """
    # no need to expose this class globally 
    class CallLaterDynDnsClient(object):
        "Minimal class to handle all of the dyndns logic using callbacks started from the reactor loop"
        def __init__(self, dyndnsclient, callLaterMethod, sleeptime):
            """
            @param dyndnsclient: a dyndnsclient object
            @param callLaterMethod: the twisted reactors callLater method
            @param sleeptime: how long to wait until callLater (secs)
            """
            self.sleeptime = sleeptime
            self.client = dyndnsclient 
            self.callLaterMethod = callLaterMethod
            # do an initial synchronization:
            self.client.sync()
    
        def check(self):
            "this will make the dyndns client check its state and also insert an additional callLater timer"
            self.client.check()
            self.callLaterMethod(self.sleeptime, self.check)

    # actual method
    dyndnsc.logger = logger
    config = getDynDnsConfiguration(angelConfig)
    if config is None:
        return None
    client = dyndnsc.getDynDnsClientForConfig(config)
    if not client is None:
        return CallLaterDynDnsClient(client, callLaterMethod, config['sleeptime'])
    else:
        return None

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
    from angel_app.config import config
    AngelConfig = config.getConfig()
    providerport = AngelConfig.getint("provider", "listenPort")
    repository = AngelConfig.get("common", "repository")

    from angel_app.resource.local.external import resource
    root = resource.External(repository)

    from twisted.web2 import server
    from twisted.web2 import channel
    from twisted.internet import reactor
    if AngelConfig.getboolean("provider", "useIPv6"):
        from angel_app.ipv6 import reactor as ignored
    site = server.Site(root)
    reactor.listenTCP(providerport, channel.HTTPFactory(site), 50) 
    getLogger().info("Listening on port %d and serving content from %s" % (providerport, repository))

    # initial test version to integrate a dyndns client into the provider loop
    dyndnsclient = getCallLaterDynDnsClientForAngelConfig(AngelConfig, callLaterMethod = reactor.callLater, logger = getLogger('dyndns'))
    if not dyndnsclient is None:
        reactor.callLater(1, dyndnsclient.check) 
    reactor.run()
    getLogger().info("Quit")

def boot():
    from optparse import OptionParser
    bootInit()
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

    appname = "provider"
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
            loghandlers.append('growl')

    initializeLogging(appname, loghandlers)

    if angelConfig.get(appname, 'enable') == False:
        from angel_app.log import getLogger
        getLogger().info("%s process is disabled in the configuration, quitting." % appname)
        sys.exit(0)

    if len(options.daemon) > 0:
        from angel_app.proc import daemonizer
        daemonizer.startstop(action=options.daemon, stdout=appname+'.stdout', stderr=appname+'.stderr', pidfile=appname+'.pid')

    return options


if __name__ == '__main__':
    options = boot()
    dance(options)