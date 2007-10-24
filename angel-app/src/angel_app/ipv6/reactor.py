"""
Monkey-patch the reactor. Import this module after importing twisted.internet.reactor to modify the
reactor to accept IPv6 connections rather than IPv4 connections.
"""
import angel_app.ipv6.tcp as tcp
from twisted.internet import reactor

def listenTCP(self, port, factory, backlog=50, interface=''):
#def listenTCP(port, factory, backlog=50, interface=''):
    """
    Stolen from twisted.internet.posixbase
    
    @see: twisted.internet.interfaces.IReactorTCP.listenTCP
    """
    p = tcp.IPv6Port(port, factory, backlog, interface, self)
    p.startListening()
    return p


# override reactor's (IPv4-only) listenTCP
#reactor.listenTCP = listenTCP
import new
reactor.listenTCP = new.instancemethod(listenTCP, reactor, reactor.__class__)
#setattr(reactor, "listenTCP", listenTCP)
