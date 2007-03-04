"""
Master process. Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""

from optparse import OptionParser
from twisted.internet.protocol import Protocol, Factory, ProcessProtocol
from twisted.internet import reactor
import os
import angel_app.logserver
import angel_app.procmanager
from angel_app.log import getLogger

def bootInit():
    """
    Method to be called in __main__ before anything else. This method cannot rely on any
    framework being initialised, e.g. no logging, no exception catching etc.
    """
    import angel_app.config.globals
    angel_app.config.globals.appname = "master"

def postConfigInit():
    """
    Run this method after the config system is initialized.
    """
    from angel_app.admin.directories import makeDirectories
    makeDirectories()

    # setup our internal temporary path for files:
    from angel_app import singlefiletransaction
    singlefiletransaction.purgeTmpPathAndSetup()

def startProcesses(binpath = os.getcwd(), privateMode = False):
    procManager = angel_app.procmanager.ExternalProcessManager()
    procManager.registerProcessStarter(reactor.spawnProcess)
    procManager.registerDelayedStarter(reactor.callLater) 

    import sys
    
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
         apps.append( (angel_app.procmanager.PresenterProtocol(), "presenter.py") )

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
    bootInit()
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

    # setup/configure logging
    import angel_app.log
    angel_app.log.setup()

    binpath = os.getcwd() # get the binpath before daemonizing (which switches to root directory of filessystem)
    angel_app.log.enableHandler('file')
    if len(options.daemon) > 0:
        from angel_app import daemonizer
        daemonizer.startstop(action=options.daemon, stdout='master.stdout', stderr='master.stderr', pidfile='master.pid')
    else:
        angel_app.log.enableHandler('console')
    angel_app.log.getReady()

    angel_app.logserver.startLoggingServer()

    from angel_app.admin import initializeRepository
    initializeRepository.initializeRepository()

    # end bootsprapping, bring on the dancing girls!

    startProcesses(binpath, options.private)

    reactor.run()    

if __name__ == "__main__":
    main()