"""
Master process. Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""

from twisted.internet import reactor

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
    singlefiletransaction.purgeTmpPathAndSetup()

def startProcesses(binpath = None, privateMode = False):
    import os
    import sys
    import angel_app.procmanager
    procManager = angel_app.procmanager.ExternalProcessManager()
    procManager.registerProcessStarter(reactor.spawnProcess)
    procManager.registerDelayedStarter(reactor.callLater) 

    if binpath == None: binpath = os.getcwd()
    
    if "PYTHONPATH" in os.environ.keys():
        os.environ["PYTHONPATH"] += ":" + os.sep.join(binpath.split(os.sep)[:-1])
    else:
        os.environ["PYTHONPATH"] = os.sep.join(binpath.split(os.sep)[:-1])

    from angel_app.config.config import getConfig
    angelConfig = getConfig()
    cfg = angelConfig.getConfigFilename()

    apps = [
         (angel_app.procmanager.ProviderProtocol(), "provider.py"), 
         (angel_app.procmanager.MaintainerProtocol(), "maintainer.py")
         ]
    if privateMode == False:
         apps.append((angel_app.procmanager.PresenterProtocol(), "presenter.py"))

    for protocol, scriptName in apps:
        process = angel_app.procmanager.ExternalProcess()
        process.setProtocol(protocol)
        # always use the interpreter we were called with
        process.setExecutable(sys.executable)
        process.setArgs(args = [sys.executable, os.path.join(binpath, scriptName), '-l', '-c', cfg])
        procManager.startServicing(process)


def py2appletWorkaroundIgnoreMe():
    """
    Import the other binaries, so py2applet takes them along in the packaging process.
    """
    import maintainer, presenter, provider



def main():
    import os
    bootInit()
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
    parser.add_option("-p", "--private", dest="private", help="private mode (no presenter)", action="store_true", default=False)
    (options, args) = parser.parse_args()

    # setup/configure config system
    from angel_app.config.config import getConfig
    angelConfig = getConfig(options.config)
    postConfigInit()
    angelConfig.bootstrapping = False

    appname = "master"

    # setup/configure logging
    from angel_app.log import initializeLogging
    loghandlers = ['file']
    if len(options.daemon) == 0: # not in daemon mode, so we log to console!
        loghandlers.append('console')
    initializeLogging(appname, loghandlers)

    from angel_app.admin import initializeRepository
    initializeRepository.initializeRepository()

    binpath = os.getcwd() # get the binpath before daemonizing (which switches to root directory of the filessystem)
    if len(options.daemon) > 0:
        from angel_app import daemonizer
        daemonizer.startstop(action=options.daemon, stdout=appname+'.stdout', stderr=appname+'.stderr', pidfile=appname+'.pid')

    # we must start the logging server after daemonizing, because we might get a port already in use otherwise (stop/restart)
    import angel_app.logserver
    angel_app.logserver.startLoggingServer()
    
    # start processes _after_ starting the logging server!
    startProcesses(binpath, options.private)

def twistedLoop():
    reactor.run()

if __name__ == "__main__":
    main()
    twistedLoop()
