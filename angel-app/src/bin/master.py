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
		endedProc(self, reason)

"""
the next 3 classes are merely here for providing a specific class name for each external process we run
"""
class PresenterProtocol(ExternalProcessProtocol):
	pass
class ProviderProtocol(ExternalProcessProtocol):
	pass
class MaintainerProtocol(ExternalProcessProtocol):
	pass

class Process():
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
	
	def registerProcessStarter(self, callback):
		self.starter = callback

	def registerDelayedStarter(self, callback):
		self.delayedstarter = callback
	
	def startServicing(self, processObj):
		"""
		Will start and eventually restart the given process
		"""
		processObj.wantDown = False
		getLogger().debug("startServicing called")
		#self.procDict[processObj] = 1
		if not self.procDict.has_key(processObj):
			getLogger().debug("process is not known")
#			if delay > 0:
#				transport = self.delayedstarter(delay, self.startProcess, processObj)
#			else:
			self.startProcess(processObj)
			self.procDict[processObj] = 1
		else:
			getLogger().warn("service for this process already known")
			if self.isAlive(processObj):
				getLogger().debug("service wants to be started but is still alive.")
			else:
				getLogger().debug("service wants to be started and is not alive!")
				self.startProcess(processObj)
				self.procDict[processObj] = 1

	def startProcess(self,processObj):
		if not processObj.wantDown:
			transport = self.starter(processObj.protocol, processObj.executable, processObj.args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)
			processObj.setTransport(transport)
			return True
		else:
			return False
		
	def stopProcess(self,processObj):
		getLogger().warn("killing process")
		if not processObj.transport == None:
			getLogger().warn("really killing process")
			try:
				res = processObj.transport.signalProcess("KILL")
			except twisted.internet.error.ProcessExitedAlready:
				getLogger().debug("Could not kill, process is down already")
			else:
				getLogger().info("process was killed")
			
		return True

	def isAlive(self, processObj):
		if not processObj.transport:
			getLogger().warn("process has no transport, cannot signal(0)")
			return False
		else:
			getLogger().debug("process found, signal(0)")
			return processObj.transport.signal(0)

	def stopServicing(self, processObj):
		"""
		Will stop the given process
		"""
		processObj.wantDown = True
		self.stopProcess(processObj)

	def restartServicing(self, processObj):
		"""
		Will stop the given process
		"""
		# TODO
		#self.stopServicing(processObj)
		#self.startServicing(processObj, 5)
		pass

	def __findProcessWithProtocol(self, protocol):
		for k, v in self.procDict.iteritems():
			if k.protocol == protocol:
				return k
		getLogger().error("Could not find the process that ended")
		raise NameError, "Could not find the process that ended"
		
	def endedProcess(self, protocol, reason):
		getLogger().error("proc ended")
		processObj = self.__findProcessWithProtocol(protocol) # TODO: catch exception
		processObj.transport = None
		self.startProcess(processObj)
		#return
		#if reason.value.exitCode == 0:
		#	startServicing(processObj, 0)
		#else:
		#	startServicing(processObj, 5)
		#	pass
		#reactor.callLater(5, startProc, protocol.__class__.__name__)
		#pass

def endedProc(protocol, reason):
	"""
	Callback for the ProcessProtocol 'processEnded' event
	"""
	procManager.endedProcess(protocol, reason)
	return
	#getLogger().warn("exit code: '%s'" , reason.value.exitCode)
	#if not reason.value.exitCode == 0:
	#	pass
	#if not wantDown:
	#	reactor.callLater(5, startProc, protocol.__class__.__name__)

	
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

	factory = Factory()
	factory.protocol = LoggingProtocol
	from logging.handlers import DEFAULT_TCP_LOGGING_PORT
	reactor.listenTCP(DEFAULT_TCP_LOGGING_PORT, factory)

	procManager = ExternalProcessManager()
	procManager.registerProcessStarter(reactor.spawnProcess)
	procManager.registerDelayedStarter(reactor.callLater) 
	
	executable = "python"
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
	

	#reactor.callLater(5, procManager.stopProcess,presenterProcess)

	reactor.run()