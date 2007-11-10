"""
Network logging server for angel-app
"""

legalMatters = """See LICENSE for details."""
__author__ = """Paul Kremer, 2007"""

"""
"""

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import logging
from angel_app.log import getLogger
import struct
import cPickle

log = getLogger(__name__)

class LoggingProtocol(Protocol):
    """
    Logging protocol as given by the "standard" python logging module and
    its SocketHandler: http://docs.python.org/lib/network-logging.html
    """
    def connectionMade(self):
        self.buf = ''
        self.slen = 0
        log.debug("Incoming logging connection from %s", self.transport.getPeer())
        if (not hasattr(self.factory, "numProtocols")):
            self.factory.numProtocols = 0
        self.factory.numProtocols = self.factory.numProtocols+1 
        #log.debug("numConnections %d" , self.factory.numProtocols)
        if self.factory.numProtocols > 20:
            self.transport.write("Too many connections, try later") 
            log.warn("Too many incoming logging connections. Dropping connection from '%s'.", self.transport.getPeer())
            self.transport.loseConnection()

    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols-1

    def dataReceived(self, data):
        self.buf += data
        # first 4 bytes specify the length of the pickle
        while len(self.buf) >= 4:
            if self.slen == 0:
                log.debug("buf longer than 4, finding length of pickle")
                self.slen = struct.unpack(">L", self.buf[0:4])[0]
            log.debug("length of pickle: %s" % str(self.slen))
            log.debug("buffer length: %s" % str( len(self.buf)-4))
            if (len(self.buf)-4 >= self.slen):
                try:
                    obj = cPickle.loads(self.buf[4:self.slen+4])
                except:
                    log.error("Problem unpickling")
                else:
                    record = logging.makeLogRecord(obj)
                    self.handleLogRecord(record)
                self.buf = self.buf[self.slen+4:]
                self.slen = 0
            else:
                log.debug("not enough in the buffer to unpickle")
                break

    def handleLogRecord(self, record):
        dummylogger = logging.getLogger(record.name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        #print record
        #logger.handle(record)
        getLogger(record.name).handle(record)


def startLoggingServer():
    """
    Will start listening to the configured tcp port using the twisted reactor.listenTCP() call
    """
    factory = Factory()
    factory.protocol = LoggingProtocol
    from angel_app.config.config import getConfig
    angelConfig = getConfig()
    reactor.listenTCP(angelConfig.getint("common", "loglistenport"), factory)
    #print "LOGGING STARTED"
