from twisted.web2.client.http import HTTPClientProtocol, ClientRequest
from twisted.python import log
from twisted.web2 import stream
from twisted.internet import protocol




def testConn(host = "localhost"):
    from twisted.internet import reactor
    d = protocol.ClientCreator(reactor, HTTPClientProtocol).connectTCP(host, 9999)
    def gotResp(resp, num):
        def print_(n):
            print "DATA %s: %r" % (num, n)
        def printdone(n):
            print "DONE %s" % num
        print "GOT RESPONSE %s: %s" % (num, resp)
        stream.readStream(resp.stream, print_).addCallback(printdone)
    def sendReqs(proto):
        log.err("sending request")
        proto.submitRequest(ClientRequest("GET", "/", {'Host':host}, None)).addCallback(gotResp, 1)
        proto.submitRequest(ClientRequest("GET", "/foo", {'Host':host}, None)).addCallback(gotResp, 2)
    d.addCallback(sendReqs)
    del d
    reactor.run()
 
# nah, not here   
#testConn()

from angel_app.maintainer.util import treeMap, inspectResource
from angel_app.maintainer import setup
setup.setupDefaultPeers()
#for item in treeMap(inspectResource): pass
