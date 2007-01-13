"""
Master process. Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""

from optparse import OptionParser
from twisted.internet.protocol import Protocol, Factory, ProcessProtocol
from twisted.internet import reactor
import os
import logging
from angel_app.log import getLogger

def bootInit():
	"""
	Method to be called in __main__ before anything else. This method cannot rely on any
	framework being initialised, e.g. no logging, no exception catching etc.
	"""
	import angel_app.config.defaults
	angel_app.config.defaults.appname = "master"


class ExternalProcessProtocol(ProcessProtocol):
	"""
	Protocol for an external process.
	This is the base class for each external process we are going to start.
	The reason to have a different class for every external process is so
	we can map the class to a specific external program.
	This class shall not be used directly. It must be used as a base class!
	"""
	def connectionMade(self):
		self.transport.closeStdin()

	def outReceived(self, data):
		getLogger(self.__class__.__name__).debug("STDOUT from '%s': %s", self.__class__.__name__, data)

	def errReceived(self, data):
		getLogger(self.__class__.__name__).debug("STDERR from '%s': %s", self.__class__.__name__, data)

	def processEnded(self, reason):
		getLogger().info("external Process with protocol '%s' ended with reason: '%s'" , self.__class__.__name__, reason.getErrorMessage())
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

class Process:
	def setProtocol(self, protocol):
		self.protocol = protocol
	def setExecutable(self, executable):
		self.executable = executable
	def setArgs(self, args):
		self.args = args
	def setTransport(self, val):
		self.transport = val

class ExternalProcessManager:
	def __init__(self):
		self.procDict = {}
		self.startendedprocessdelay = 5 # number of seconds to delay the restarting of an ended process
	
	def registerProcessStarter(self, callback):
		self.starter = callback

	def registerDelayedStarter(self, callback):
		self.delayedstarter = callback
	
	def startServicing(self, processObj):
		"""
		Will start and eventually restart the given process
		"""
		processObj.wantDown = False
		getLogger("ExternalProcessManager").info("startServicing %s", processObj.protocol)
		#self.procDict[processObj] = 1
		if not self.procDict.has_key(processObj):
			getLogger("ExternalProcessManager").debug("process is not known")
#			if delay > 0:
#				transport = self.delayedstarter(delay, self.startProcess, processObj)
#			else:
			self.startProcess(processObj)
			self.procDict[processObj] = 1
		else:
			getLogger("ExternalProcessManager").debug("service for this process already known")
			if self.isAlive(processObj):
				getLogger("ExternalProcessManager").debug("service wants to be started but is still alive.")
			else:
				getLogger("ExternalProcessManager").debug("service wants to be started and is not alive!")
				self.startProcess(processObj)
				self.procDict[processObj] = 1

	def startProcess(self,processObj, delay = 0):
		if not processObj.wantDown:
			if delay == 0:
				transport = self.starter(processObj.protocol, processObj.executable, processObj.args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)
				getLogger("ExternalProcessManager").info("started process '%s' with PID '%s'", processObj.protocol, transport.pid)
				processObj.setTransport(transport)
				return True
			else:
				getLogger("ExternalProcessManager").debug("delay startProcess '%s' by %d seconds", processObj.protocol, delay)
				self.delayedstarter(delay, self.startProcess, processObj)
		else:
			del self.procDict[processObj]
			return False
		
	def stopProcess(self, processObj):
		getLogger("ExternalProcessManager").info("stopping process %s", processObj.protocol)
		if not processObj.transport == None:
			getLogger("ExternalProcessManager").debug("trying to kill process")
			try:
				res = processObj.transport.signalProcess("KILL")
			except twisted.internet.error.ProcessExitedAlready:
				getLogger("ExternalProcessManager").debug("Could not kill, process is down already")
			else:
				if not self.isAlive(processObj):
					getLogger("ExternalProcessManager").debug("process was killed")
				else:
					getLogger("ExternalProcessManager").warn("process was NOT successfully killed")
		return True

	def isAlive(self, processObj):
		if not processObj.transport:
			getLogger("ExternalProcessManager").warn("process has no transport, cannot signal(0)")
			return False
		else:
			getLogger("ExternalProcessManager").debug("process found, signalProcess(0)")
			return processObj.transport.signalProcess(0)

	def stopServicing(self, processObj):
		"""
		Will stop the service for the given process
		"""
		getLogger("ExternalProcessManager").info("stop servicing %s", processObj.protocol)
		processObj.wantDown = True
		self.stopProcess(processObj)

	def restartServicing(self, processObj):
		"""
		Will stop the given process
		"""
		# TODO: this relies on the fact that once we kill a process, it must have called 'processEnded' within
		# the delay self.startendedprocessdelay, e.g. it must have effectively detached from the service monitoring
		self.stopServicing(processObj)
		self.delayedstarter(self.startendedprocessdelay, self.startServicing, processObj)

	def __findProcessWithProtocol(self, protocol):
		for k, v in self.procDict.iteritems():
			if k.protocol == protocol:
				return k
		getLogger("ExternalProcessManager").error("Could not find the process that ended")
		raise NameError, "Could not find the process that ended"
		
	def endedProcess(self, protocol, reason):
		"""
		Callback for the ProcessProtocol 'processEnded' event
		"""
		processObj = self.__findProcessWithProtocol(protocol) # TODO: catch exception
		getLogger("ExternalProcessManager").debug("process with protocol '%s' and PID '%s' ended", protocol, processObj.transport.pid)
		processObj.transport = None
		# when a process end, the default is to just start it again,
		# the start routine knows if the process must really  be started again
		# Also, we delay the starting of an ended process by self.startendedprocessdelay (seconds)
		self.startProcess(processObj, self.startendedprocessdelay)
		# TODO: check the exit code and possibly detect a broken setup?
		#if reason.value.exitCode == 0:
	
import struct
import cPickle
class LoggingProtocol(Protocol):
	"""
	Logging protocol as given by the "standard" python logging module and
	its SocketHandler: http://docs.python.org/lib/network-logging.html
	"""
	def connectionMade(self):
		self.buf = ''
		self.slen = 0
		getLogger().debug("Incoming logging connection from %s", self.transport.getPeer())
		if (not hasattr(self.factory, "numProtocols")):
			self.factory.numProtocols = 0
		self.factory.numProtocols = self.factory.numProtocols+1 
		#getLogger().debug("numConnections %d" , self.factory.numProtocols)
		if self.factory.numProtocols > 20:
			self.transport.write("Too many connections, try later") 
			getLogger().warn("Too many incoming logging connections. Dropping connection from '%s'.", self.transport.getPeer())
			self.transport.loseConnection()

	def connectionLost(self, reason):
		self.factory.numProtocols = self.factory.numProtocols-1

	def dataReceived(self, data):
		self.buf += data
		# first 4 bytes specify the length of the pickle
		while len(self.buf) >= 4:
			if self.slen == 0:
				#print "buf longer than 4, finding slen"
				self.slen = struct.unpack(">L", self.buf[0:4])[0]
			#print "slen ", self.slen
			#print "buf length: ", len(self.buf)-4
			if (len(self.buf)-4 >= self.slen):
				try:
					obj = cPickle.loads(self.buf[4:self.slen+4])
				except:
					getLogger().error("Problem unpickling")
				else:
					record = logging.makeLogRecord(obj)
					self.handleLogRecord(record)
				self.buf = self.buf[self.slen+4:]
				self.slen = 0

	def handleLogRecord(self, record):
		logger = logging.getLogger(record.name)
		# N.B. EVERY record gets logged. This is because Logger.handle
		# is normally called AFTER logger-level filtering. If you want
		# to do filtering, do it at the client end to save wasting
		# cycles and network bandwidth!
		#print record
		#logger.handle(record)
		getLogger(record.name).handle(record)


def startLoggingServer():
	factory = Factory()
	factory.protocol = LoggingProtocol
	from logging.handlers import DEFAULT_TCP_LOGGING_PORT
	reactor.listenTCP(DEFAULT_TCP_LOGGING_PORT, factory)

def startProcessesWithProcessManager(procManager):
	procManager.registerProcessStarter(reactor.spawnProcess)
	procManager.registerDelayedStarter(reactor.callLater) 
	
	executable = "python" # TODO: get exact python binary!
	binpath = os.path.join(os.getcwd(),"bin") # TODO: where are the scripts?

	presenterProcess = Process()
	presenterProcess.setProtocol(PresenterProtocol())
	presenterProcess.setExecutable(executable)
	presenterProcess.setArgs(args = [executable, os.path.join(binpath,"presenter.py"), '-l']) 
	procManager.startServicing(presenterProcess)
	
	providerProcess = Process()
	providerProcess.setProtocol(ProviderProtocol())
	providerProcess.setExecutable(executable)
	providerProcess.setArgs(args = [executable, os.path.join(binpath,"provider.py"), '-l']) 
	procManager.startServicing(providerProcess)
	
	maintainerProcess = Process()
	maintainerProcess.setProtocol(MaintainerProtocol())
	maintainerProcess.setExecutable(executable)
	maintainerProcess.setArgs(args = [executable, os.path.join(binpath,"maintainer.py"), '-l']) 
	procManager.startServicing(maintainerProcess)

	#test/debug code:
#	testProcess = Process()
#	testProcess.setProtocol(TestProtocol())
#	testProcess.setExecutable("/sw/bin/sleep")
#	testProcess.setArgs(args = ["/sw/bin/sleep", '5']) 
#	procManager.startServicing(testProcess)
#	reactor.callLater(4, procManager.restartServicing, presenterProcess)
	

if __name__ == "__main__":
	bootInit()
	parser = OptionParser()
	parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
	(options, args) = parser.parse_args()

	import angel_app.log
	angel_app.log.setup()

	angel_app.log.enableHandler('file')
	if len(options.daemon) > 0:
		from angel_app import proc
		proc.startstop(action=options.daemon, stdout='master.stdout', stderr='master.stderr', pidfile='master.pid')
	else:
		angel_app.log.enableHandler('console')
	angel_app.log.getReady()

	startLoggingServer()

	# ExternalProcessManager.processEnded must be available to the ProcessProtocol, otherwise callbacks won't work
	# that's why we instantiate it here in __main__
	procManager = ExternalProcessManager()
	startProcessesWithProcessManager(procManager)

	reactor.run()