import sys

# dyndns: initial test. Should probably go somewhere else than this module
import angel_app.contrib.dyndnsc as dyndnsc

def getDynDnsConfiguration(AngelConfig):
    "fetches dyndns configuration, if unconfigured, returns None"
    cfg = {}
    try:
        cfg['hostname'] = AngelConfig.get('dyndns', 'hostname') 
        cfg['updatekey'] = AngelConfig.get('dyndns', 'updatekey') 
    except:
        return None
    else:
        return cfg

class AngelDynDnsClient(object):
    "Minimal class to handle all of the dyndns logic using callbacks started from the reactor loop"
    def __init__(self, config, callLaterMethod):
        """
        @param config: a dictionary object
        @param callLaterMethod: the twisted reactors callLater method
        """
        sleeptime = 60
        hostname = config['hostname'] 
        key = config['updatekey'] 
        
        dnsChecker = dyndnsc.IPDetector_DNS()
        dnsChecker.setHostname(hostname)
    
        protoHandler = dyndnsc.DyndnsUpdateProtocol(hostname = hostname, key = key)
    
        dyndnsclient = dyndnsc.DynDnsClient( sleeptime = sleeptime)
        dyndnsclient.setProtocolHandler(protoHandler)
        dyndnsclient.setDNSDetector(dnsChecker)
        dyndnsclient.setChangeDetector(dyndnsc.IPDetector_TeredoOSX())
        self.client = dyndnsclient 
        self.callLaterMethod = callLaterMethod

        # do an initial synchronization:
        self.client.sync()

    def check(self):
        "call this regularily to ensure dns is up to date"
        self.client.check()
        self.callLaterMethod(60, self.check)


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
    getLogger().info("Listening on port %d and serving content from %s", providerport, repository)

    # initial test version to integrate a dyndns client into the provider loop
    dyndnscfg = getDynDnsConfiguration(AngelConfig)
    if not dyndnscfg is None: # if it's configured
        dyndnsclient = AngelDynDnsClient(config = dyndnscfg, callLaterMethod = reactor.callLater)
        reactor.callLater(60, dyndnsclient.check)
    reactor.run()

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