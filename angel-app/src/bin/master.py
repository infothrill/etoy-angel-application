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
    import angel_app.config.defaults
    angel_app.config.defaults.appname = "master"
    # setup and cleanup our internal temporary path for files:

def postConfigInit():
    """
    Run this method after the config system is initialized.
    """
    from angel_app.admin.directories import makeDirectories
    makeDirectories()

    # setup our internal temporary path for files:
    from angel_app import singlefiletransaction
    singlefiletransaction.purgeTmpPathAndSetup()

def startProcesses(binpath = os.getcwd()):
    procManager = angel_app.procmanager.ExternalProcessManager()
    procManager.registerProcessStarter(reactor.spawnProcess)
    procManager.registerDelayedStarter(reactor.callLater) 
    
    # if binpath has a python interpreter, we use it:
    if (os.path.exists(os.path.join(binpath, "python"))):
        executable = os.path.join(binpath, "python")
    else:
        executable = "python" # system installation (must be in environ.PATH)
    
    if "PYTHONPATH" in os.environ.keys():
        os.environ["PYTHONPATH"] += ":" + os.sep.join(os.sep.split(binpath)[:-1])
    else:
        os.environ["PYTHONPATH"] = os.sep.join(os.sep.split(binpath)[:-1])

    cfg = angelConfig.getConfigFilename()

    presenterProcess = angel_app.procmanager.ExternalProcess()
    presenterProcess.setProtocol(angel_app.procmanager.PresenterProtocol())
    presenterProcess.setExecutable(executable)
    presenterProcess.setArgs(args = [executable, os.path.join(binpath,"presenter.py"), '-l', '-c', cfg]) 
    procManager.startServicing(presenterProcess)
    
    providerProcess = angel_app.procmanager.ExternalProcess()
    providerProcess.setProtocol(angel_app.procmanager.ProviderProtocol())
    providerProcess.setExecutable(executable)
    providerProcess.setArgs(args = [executable, os.path.join(binpath,"provider.py"), '-l', '-c', cfg]) 
    procManager.startServicing(providerProcess)
    
    maintainerProcess = angel_app.procmanager.ExternalProcess()
    maintainerProcess.setProtocol(angel_app.procmanager.MaintainerProtocol())
    maintainerProcess.setExecutable(executable)
    maintainerProcess.setArgs(args = [executable, os.path.join(binpath,"maintainer.py"), '-l', '-c', cfg]) 
    procManager.startServicing(maintainerProcess)

    #test/debug code:
#    testProcess = angel_app.procmanager.ExternalProcess()
#    testProcess.setProtocol(angel_app.procmanager.TestProtocol())
#    testProcess.setExecutable("/sw/bin/sleep")
#    testProcess.setArgs(args = ["/sw/bin/sleep", '5']) 
#    procManager.startServicing(testProcess)
#    reactor.callLater(4, procManager.restartServicing, presenterProcess)

def py2appletWorkaroundIgnoreMe():
    """
    Import the other binaries, so py2applet takes them along in the packaging process.
    """
    import maintainer, presenter, provider
        

if __name__ == "__main__":
    bootInit()
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
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
        from angel_app import daemonizer
        daemonizer.startstop(action=options.daemon, stdout='master.stdout', stderr='master.stderr', pidfile='master.pid')
    else:
        angel_app.log.enableHandler('console')
    angel_app.log.getReady()

    angel_app.logserver.startLoggingServer()

    # end bootsprapping, bring on the dancing girls!

    startProcesses()

    reactor.run()