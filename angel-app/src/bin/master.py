"""
Master process. Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""

from twisted.internet.protocol import Protocol, Factory, ProcessProtocol
from twisted.internet import reactor
import cPickle
import os
import logging

class externalprocessProtocol(ProcessProtocol):
	"""
	Simplistic Protocol for an external process.
	TODO: probably we need a protocol for each process we want to start, so
	we can control what's happening. E.g. we don't know which process
	died for example.
	"""
	def connectionMade(self):
		print "external Process started\n" # TODO

	def outReceived(self, data):
		print data # TODO : this is temporary until we know how to use stdout/stderr
		pass

	def processEnded(self, reason):
		print "external Process ENDED" + reason.getErrorMessage() + "!" # TODO

class LoggingProtocol(Protocol):
	"""
	Simplistic logging protocol as given by the "standard" python logging module and
	its SocketHandler: http://docs.python.org/lib/network-logging.html
	"""
	def connectionMade(self):
		print "Incoming logging connection"
		if (not hasattr(self.factory, "numProtocols")):
			self.factory.numProtocols = 0
		self.factory.numProtocols = self.factory.numProtocols+1 
		if self.factory.numProtocols > 4:
			self.transport.write("Too many connections, try later") 
			self.transport.loseConnection()

		def connectionLost(self, reason):
			self.factory.numProtocols = self.factory.numProtocols-1

	def dataReceived(self, data):
		# first 4 bytes specify the length, only useful when doing select()/read()
		obj = cPickle.loads(data[4:])
		record = logging.makeLogRecord(obj)
		self.handleLogRecord(record)

	def handleLogRecord(self, record):
		logger = logging.getLogger(record.name)
		# N.B. EVERY record gets logged. This is because Logger.handle
		# is normally called AFTER logger-level filtering. If you want
		# to do filtering, do it at the client end to save wasting
		# cycles and network bandwidth!
		logger.handle(record)

if __name__ == "__main__":
	logging.basicConfig(format="%(name)-15s %(levelname)-8s %(message)s") # TODO

	factory = Factory()
	factory.protocol = LoggingProtocol	
	reactor.listenTCP(9020, factory)

	processProtocol = externalprocessProtocol()

	executable = "python"

	args = ["python", os.path.join(os.getcwd(),"bin/presenter.py"), '-l']	  
	presenterTransport = reactor.spawnProcess(processProtocol, executable, args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)

	args = ["python", os.path.join(os.getcwd(),"bin/provider.py"), '-l']	  
	providerTransport = reactor.spawnProcess(processProtocol, executable, args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)

	# TODO: add maintainer	

	reactor.run()
