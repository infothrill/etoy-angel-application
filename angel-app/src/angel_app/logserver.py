"""
Network logging server for angel-app
"""

legalMatters = """
 Copyright (c) 2006, etoy.VENTURE ASSOCIATION
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without modification, 
 are permitted provided that the following conditions are met:
 *  Redistributions of source code must retain the above copyright notice, 
    this list of conditions and the following disclaimer.
 *  Redistributions in binary form must reproduce the above copyright notice, 
    this list of conditions and the following disclaimer in the documentation 
    and/or other materials provided with the distribution.
 *  Neither the name of etoy.CORPORATION nor the names of its contributors may be used to 
    endorse or promote products derived from this software without specific prior 
    written permission.
 
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY 
 EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
 OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT 
 SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
 SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT 
 OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) 
 HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
 OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS 
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
"""

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
