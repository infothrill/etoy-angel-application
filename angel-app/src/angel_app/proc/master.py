"""
This module contains code to start the master process correctly, e.g. it contains mostly
bootstrapping-code for the process.
"""

from angel_app.proc.common import postConfigInit

def bootInit():
    """
    Method to be called in __main__ before anything else. This method cannot rely on any
    framework being initialised, e.g. no logging, no config etc.
    """
    pass

def boot():
    from optparse import OptionParser
    bootInit()
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
    parser.add_option("-p", "--private", dest="private", help="private mode (no presenter)", action="store_true", default=False)
    (options, dummyargs) = parser.parse_args()

    appname = "master"

    # setup/configure config system
    from angel_app.config.config import getConfig
    angelConfig = getConfig(options.config)
    postConfigInit()
    angelConfig.bootstrapping = False

    # setup/configure logging
    from angel_app.log import initializeLogging
    loghandlers = ['file']
    if len(options.daemon) == 0: # not in daemon mode, so we log to console!
        loghandlers.append('console')
    initializeLogging(appname, loghandlers)

    import angel_app.proc.procmanager # import before daemonizing

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

    import angel_app.logserver
    import angel_app.proc.procmanager
    angel_app.logserver.startLoggingServer()
    # start processes _after_ starting the logging server!
    angel_app.proc.procmanager.startProcesses(options.private)
    from twisted.internet import reactor
    reactor.run()
    
if __name__ == '__main__':
    options = boot()
    dance(options)
