"""
Master process. Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""

from optparse import OptionParser
from twisted.internet.protocol import Protocol, Factory, ProcessProtocol
from twisted.internet import reactor
import os
import angel_app.logserver
from angel_app.log import getLogger

def bootInit():
	"""
	Method to be called in __main__ before anything else. This method cannot rely on any
	framework being initialised, e.g. no logging, no exception catching etc.
	"""
	import angel_app.config.defaults
	angel_app.config.defaults.appname = "master"


class ExternalProcessProtocol(ProcessProtocol):
	from angel_app.log import getLogger
	"""
	Protocol for an external process.
	This is the base class for each external process we are going to start.
	The reason to have a different class for every external process is so
	we can map the class to a specific external program.
	This class shall not be used directly. It must be used as a base class!
	"""
	def __init__(self):
		self.log = getLogger(self.__class__.__name__)

	def connectionMade(self):
		self.transport.closeStdin()

	def outReceived(self, data):
		self.log.debug("STDOUT from '%s': %s", self.__class__.__name__, data)

	def errReceived(self, data):
		self.log.debug("STDERR from '%s': %s", self.__class__.__name__, data)

	def processEnded(self, reason):
		self.log.info("external Process with protocol '%s' ended with reason: '%s'" , self.__class__.__name__, reason.getErrorMessage())
		procManager.endedProcess(self, reason)

"""
the next 3 classes are merely here for providing a specific class name for each external process we run
"""
class PresenterProtocol(ExternalProcessProtocol):
	pass
class ProviderProtocol(ExternalProcessProtocol):
	pass
class MaintainerProtocol(ExternalProcessProtocol):
	pass
class TestProtocol(ExternalProcessProtocol):
	pass

class ExternalProcess:
	"""
	Class to represent an external process. It really is just a container for
	some variables.
	"""
	def __init__(self):
		self.failures = 0 # number of times it exited with non-zero exit code
	def setProtocol(self, protocol):
		self.protocol = protocol
	def setExecutable(self, executable):
		self.executable = executable
	def setArgs(self, args):
		self.args = args
	def setTransport(self, val):
		self.transport = val

class ExternalProcessManager:
	"""
	This class can be used to manage (start/stop/restart) forked off
	processes. It uses the twisted matrix library and its
	ability to asynchronously attach and detach such processes.
	To enable interaction between the twisted reactor and this class, it
	must be instantiated in the same scope than the twisted reactor, the callbacks
	work. Also, a single external process is described by an object of class
	"externalProcess".
	"""
	from angel_app.log import getLogger
	def __init__(self):
		"""
		Initialize internal process dictionary, set some defaults and
		get a logger object.
		"""
		self.procDict = {}
		self.startendedprocessdelay = 5 # number of seconds to delay the restarting of an ended process
		self.log = getLogger("ExternalProcessManager")
	
	def registerProcessStarter(self, callback):
		"""
		register the given callback as the function responsible for starting a process.
		The callback will be called like so:
		callback(ExternalProcessObject.protocol, ExternalProcessObject.executable, ExternalProcessObject.args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)
		"""
		self.starter = callback

	def registerDelayedStarter(self, callback):
		"""
		register the given callback as the function responsible for starting a process in a delayed faschion.
		The callback will be called like so:
		callback(delay, self.startProcess, ExternalProcessObject)
		"""
		self.delayedstarter = callback
	
	def startServicing(self, processObj):
		"""
		Will start "servicing" the given process, e.g. also restart it in case it ends.
		Usually, you want to call this method to initially start a process that you want
		to stay alive.
		"""
		processObj.wantDown = False
		self.log.info("startServicing %s", processObj.protocol)
		if not self.procDict.has_key(processObj):
			self.log.debug("process is not known")
			self.startProcess(processObj)
			self.procDict[processObj] = 1
		else:
			self.log.debug("service for this process already known")
			if self.isAlive(processObj):
				self.log.debug("service wants to be started but is still alive.")
			else:
				self.log.debug("service wants to be started and is not alive!")
				self.startProcess(processObj)
				self.procDict[processObj] = 1

	def stopServicing(self, processObj):
		"""
		Will stop the "servicing" for the given process, e.g. it will
		attempt to stop it and also disable the servicing, so it will
		not be restarted when it dies/stops.
		"""
		self.log.info("stop servicing %s", processObj.protocol)
		processObj.wantDown = True
		self.stopProcess(processObj)

	def __restartServicing(self, processObj):
		"""
		stop and start service. Don't use. Beta.
		"""
		# TODO: this relies on the fact that once we kill a process, it must have called 'processEnded' within
		# the delay self.startendedprocessdelay, e.g. it must have effectively detached from the service monitoring
		self.stopServicing(processObj)
		self.delayedstarter(self.startendedprocessdelay, self.startServicing, processObj)

	def startProcess(self,processObj, delay = 0):
		"""
		Method to physically start the given process in asynchronous fashion.
		"""
		if not processObj.wantDown:
			if delay == 0:
				transport = self.starter(processObj.protocol, processObj.executable, processObj.args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)
				self.log.info("started process '%s' with PID '%s'", processObj.protocol, transport.pid)
				processObj.setTransport(transport)
				return True
			else:
				self.log.debug("delay startProcess '%s' by %d seconds", processObj.protocol, delay)
				self.delayedstarter(delay, self.startProcess, processObj)
				return True
		else:
			del self.procDict[processObj]
			return False
		
	def stopProcess(self, processObj):
		"""
		Method to physically stop the given process in synchronous fashion.
		"""
		self.log.info("stopping process %s", processObj.protocol)
		if not processObj.transport == None:
			self.log.debug("trying to kill process")
			try:
				res = processObj.transport.signalProcess("KILL")
			except twisted.internet.error.ProcessExitedAlready:
				self.log.debug("Could not kill, process is down already")
				return True
			else:
				if not self.isAlive(processObj):
					self.log.debug("process was killed")
					return True
				else:
					self.log.warn("process was NOT successfully killed")
					# TODO: raise exception
					return False

	def isAlive(self, processObj):
		"""
		Check if the given process is still runnning by sending it a POSIX signal
		with value 0. This might not be very portable...
		"""
		if not processObj.transport:
			self.log.warn("process has no transport, cannot signal(0)")
			return False
		else:
			self.log.debug("process found, signalProcess(0)")
			return processObj.transport.signalProcess(0)

	def endedProcess(self, protocol, reason):
		"""
		Callback for the ProcessProtocol 'processEnded' event.
		"""
		processObj = self.__findProcessWithProtocol(protocol) # TODO: catch exception
		self.log.debug("process with protocol '%s' and PID '%s' ended with exit code '%s'", protocol, processObj.transport.pid, reason.value.exitCode)
		processObj.transport = None
		if not reason.value.exitCode == 0:
			processObj.failures += 1
		if processObj.failures > 5:
			self.log.warn("service %s keeps failing!", protocol)
		if processObj.failures > 10:
			self.log.warn("Stopping service of %s because of too many failures", protocol)
			self.stopServicing(processObj)
		# when a process end, the default is to just start it again,
		# the start routine knows if the process must really  be started again
		# Also, we delay the starting of an ended process by self.startendedprocessdelay (seconds)
		self.startProcess(processObj, self.startendedprocessdelay)
	
	def __findProcessWithProtocol(self, protocol):
		for k, v in self.procDict.iteritems():
			if k.protocol == protocol:
				return k
		self.log.error("Could not find the process that ended")
		raise NameError, "Could not find the process that ended"
		

def startProcessesWithProcessManager(procManager):
	procManager.registerProcessStarter(reactor.spawnProcess)
	procManager.registerDelayedStarter(reactor.callLater) 
	
	binpath = os.getcwd()
	# if binpath has a python interpreter, we use it:
	if (os.path.exists(os.path.join(binpath, "python"))):
		executable = os.path.join(binpath, "python")
	else:
		executable = "python" # TODO: get exact python binary!
	
	if "PYTHONPATH" in os.environ.keys():
		os.environ["PYTHONPATH"] += ":" + os.sep.join(os.sep.split(binpath)[:-1])
	else:
		os.environ["PYTHONPATH"] = os.sep.join(os.sep.split(binpath)[:-1])

	presenterProcess = ExternalProcess()
	presenterProcess.setProtocol(PresenterProtocol())
	presenterProcess.setExecutable(executable)
	presenterProcess.setArgs(args = [executable, os.path.join(binpath,"presenter.py"), '-l']) 
	procManager.startServicing(presenterProcess)
	
	providerProcess = ExternalProcess()
	providerProcess.setProtocol(ProviderProtocol())
	providerProcess.setExecutable(executable)
	providerProcess.setArgs(args = [executable, os.path.join(binpath,"provider.py"), '-l']) 
	procManager.startServicing(providerProcess)
	
	maintainerProcess = ExternalProcess()
	maintainerProcess.setProtocol(MaintainerProtocol())
	maintainerProcess.setExecutable(executable)
	maintainerProcess.setArgs(args = [executable, os.path.join(binpath,"maintainer.py"), '-l']) 
	procManager.startServicing(maintainerProcess)

	#test/debug code:
#	testProcess = ExternalProcess()
#	testProcess.setProtocol(TestProtocol())
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
	procManager = ExternalProcessManager()
	startProcessesWithProcessManager(procManager)

	reactor.run()