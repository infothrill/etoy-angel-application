"""
This module contains code to start the master process correctly, e.g. it contains mostly
bootstrapping-code for the process.

Attention: due to bootstrapping issues, the sequence of imports is relevant!
"""

from angel_app.proc.common import postConfigInit

def bootInit():
    """
    Method to be called in __main__ before anything else. This method cannot rely on any
    framework being initialised, e.g. no logging, no config etc.
    """
    pass

def getProcsToStart(angelConfig):
    procsThatShouldBeExplicitlyEnabled = ['provider', 'presenter', 'maintainer']
    def enabled(procName):
        return angelConfig.getboolean(procName, 'enable')
    enabledProcs = filter(enabled, procsThatShouldBeExplicitlyEnabled)
    # we always need ZEO for DB support
    return enabledProcs + ['zeo']

def boot():
    from optparse import OptionParser
    bootInit()
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
    (options, dummyargs) = parser.parse_args()

    appname = "master"

    # setup/configure config system
    from angel_app.config.config import getConfig
    angelConfig = getConfig(options.config)
    postConfigInit()
    angelConfig.bootstrapping = False
    # find out which processes are enabled:
    options.procsToStart = getProcsToStart(angelConfig)

    # setup/configure logging
    from angel_app.log import initializeLogging
    loghandlers = ['file']
    if angelConfig.getboolean('common', 'desktopnotification'):
        loghandlers.append('growl')
    if len(options.daemon) == 0: # not in daemon mode, so we log to console!
        loghandlers.append('console')
    initializeLogging(appname, loghandlers)

    import angel_app.proc.procmanager # import before daemonizing @UnusedImport

    if len(options.daemon) > 0:
        from angel_app.proc import daemonizer
        daemonizer.startstop(action=options.daemon, stdout=appname+'.stdout', stderr=appname+'.stderr', pidfile=appname+'.pid')

    return options


def dance(options):
    """
    This method encapsulates all calls that are not framework related, e.g.
    the actual angel-app ;-)
    Also, it contains the hooks to events in the Twisted reactor.
    """
    from angel_app.admin import initializeRepository
    initializeRepository.initializeRepository()

    from angel_app.logserver import startLoggingServer
    from angel_app.proc.procmanager import startProcesses 
    startLoggingServer()
    # start processes _after_ starting the logging server!
    startProcesses(options.procsToStart)
    from twisted.internet import reactor
    from angel_app.log import getLogger
    getLogger().growl("User", "NODE ACTIVATED", "Launching sub-processes.")
    reactor.run()
    getLogger().info("Quit")

if __name__ == '__main__':
    options = boot()
    dance(options)
