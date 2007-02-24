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
	angel_app.config.defaults.binpath = os.getcwd()


def startProcessesWithProcessManager(procManager, binpath = os.getcwd()):
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

	presenterProcess = angel_app.procmanager.ExternalProcess()
	presenterProcess.setProtocol(angel_app.procmanager.PresenterProtocol())
	presenterProcess.setExecutable(executable)
	presenterProcess.setArgs(args = [executable, os.path.join(binpath,"presenter.py"), '-l']) 
	procManager.startServicing(presenterProcess)
	
	providerProcess = angel_app.procmanager.ExternalProcess()
	providerProcess.setProtocol(angel_app.procmanager.ProviderProtocol())
	providerProcess.setExecutable(executable)
	providerProcess.setArgs(args = [executable, os.path.join(binpath,"provider.py"), '-l']) 
	procManager.startServicing(providerProcess)
	
	maintainerProcess = angel_app.procmanager.ExternalProcess()
	maintainerProcess.setProtocol(angel_app.procmanager.MaintainerProtocol())
	maintainerProcess.setExecutable(executable)
	maintainerProcess.setArgs(args = [executable, os.path.join(binpath,"maintainer.py"), '-l']) 
	procManager.startServicing(maintainerProcess)

	#test/debug code:
#	testProcess = angel_app.procmanager.ExternalProcess()
#	testProcess.setProtocol(angel_app.procmanager.TestProtocol())
#	testProcess.setExecutable("/sw/bin/sleep")
#	testProcess.setArgs(args = ["/sw/bin/sleep", '5']) 
#	procManager.startServicing(testProcess)
#	reactor.callLater(4, procManager.restartServicing, presenterProcess)

def py2appletWorkaroundIgnoreMe():
	"""
	Import the other binaries, so py2applet takes them along in the packaging process.
	"""
	import maintainer, presenter, provider
		

if __name__ == "__main__":
	bootInit()
	parser = OptionParser()
	parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
	(options, args) = parser.parse_args()

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

	# ExternalProcessManager.processEnded must be available to the ProcessProtocol, otherwise callbacks won't work
	# that's why we instantiate it here in __main__
	procManager = angel_app.procmanager.ExternalProcessManager()
	startProcessesWithProcessManager(procManager, angel_app.config.defaults.binpath)

	reactor.run()