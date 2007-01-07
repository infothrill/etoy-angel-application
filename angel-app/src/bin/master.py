"""
Master process. Responsible for starting all relevant angel-app components
(presenter, provider, maintainer), does the logging as well.
"""

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
	we can map the class to a specific program.
	"""
	def connectionMade(self):
		getLogger().info("external Process with protocol '%s' started", self.__class__.__name__)

	def outReceived(self, data):
		print data # TODO : this is temporary until we know how to use stdout/stderr
		pass

	def processEnded(self, reason):
		getLogger().warn("external Process with protocol '%s' ended with reason: '%s'" , self.__class__.__name__, reason.getErrorMessage())
		endedProc(self.__class__.__name__)

class presenterProtocol(ExternalProcessProtocol):
	def dummy():
		pass
class providerProtocol(ExternalProcessProtocol):
	def dummy():
		pass
class maintainerProtocol(ExternalProcessProtocol):
	def dummy():
		pass

##############################
wantDown = False # set this to true when you want to shutdown cleanly!
def endedProc(name):
	getLogger().debug("proc  protocol '%s' ended", name)
	if not wantDown:
		import time
		time.sleep(5) # TODO: use some sort of Deferred to delay the starting!
		startProc(name)
def startProc(name):
	import re
	executable = "python"
	if re.match('^presenter.*', name):
		proto = presenterProtocol()
		args = ["python", os.path.join(os.getcwd(),"bin/presenter.py"), '-l']
		presenterTransport = reactor.spawnProcess(proto, executable, args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)
	if re.match('^provider.*', name):
		proto = providerProtocol()
		args = ["python", os.path.join(os.getcwd(),"bin/provider.py"), '-l']
		providerTransport = reactor.spawnProcess(proto, executable, args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)
	if re.match('^maintainer.*', name):
		proto = maintainerProtocol()
		args = ["python", os.path.join(os.getcwd(),"bin/maintainer.py"), '-l']
		providerTransport = reactor.spawnProcess(proto, executable, args, env=os.environ, path='/', uid=None, gid=None, usePTY=True)
	# give the proc a chance to start:
	import time
	time.sleep(1)
##############################

import struct
import cPickle
class LoggingProtocol(Protocol):
	"""
	Simplistic logging protocol as given by the "standard" python logging module and
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
		if self.factory.numProtocols > 100:
			self.transport.write("Too many connections, try later") 
			#getLogger().warn("Too many incoming logging connections. Dropping.")
			self.transport.loseConnection()

		def connectionLost(self, reason):
			self.factory.numProtocols = self.factory.numProtocols-1

	def dataReceived(self, data):
		self.buf += data
		# first 4 bytes specify the length of the pickle
		if len(self.buf) >= 4:
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
					self.buf = self.buf[self.slen+4:]
					self.slen = 0
					record = logging.makeLogRecord(obj)
					self.handleLogRecord(record)

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
	import angel_app.log
	angel_app.log.setup()
	angel_app.log.enableHandler('console')
	angel_app.log.enableHandler('file')
	angel_app.log.getReady()

	factory = Factory()
	factory.protocol = LoggingProtocol
	from logging.handlers import DEFAULT_TCP_LOGGING_PORT
	reactor.listenTCP(DEFAULT_TCP_LOGGING_PORT, factory)

	startProc('presenter')
	startProc('provider')
	#startProc('maintainer')

	reactor.run()