from twisted.internet import tcp
from zope.interface import implements
from twisted.internet.interfaces import IAddress
import socket

class IPv6Address(object):
    """
    Object representing an IPv6 socket endpoint. Copy-pasted from twisted.internet.tcp.address

    @ivar type: A string describing the type of transport, either 'TCP' or 'UDP'.
    @ivar host: A string containing the dotted-quad IP address.
    @ivar port: An integer representing the port number.
    """

    # _bwHack is given to old users who think we are a tuple. They expected
    # addr[0] to define the socket type rather than the address family, so
    # the value comes from a different namespace than the new .type value:
    
    #  type = map[_bwHack]
    # map = { 'SSL': 'TCP', 'INET': 'TCP', 'INET_UDP': 'UDP' }

    implements(IAddress)
 
    def __init__(self, type, host, port, _bwHack = None):
        assert type in ('TCP', 'UDP')
        self.type = type
        self.host = host
        self.port = port
        self._bwHack = _bwHack

    
    def __eq__(self, other):
        if isinstance(other, tuple):
            return tuple(self) == other
        elif isinstance(other, IPv6Address):
            a = (self.type, self.host, self.port)
            b = (other.type, other.host, other.port)
            return a == b
        return False

    def __str__(self):
        return 'IPv6Address(%s, %r, %d)' % (self.type, self.host, self.port)

class IPv6Server(tcp.Server):
    
    def __init__(self, sock, protocol, client, server, sessionno):
        super(IPv6Server, self).__init__(sock, protocol, client, server, sessionno)
        
    def getHost(self):
        """
        @return my IPv6Address
        """
        aa = self.socket.getsockname()
        return IPv6Address('TCP', *((aa[0], aa[1]) + ('INET',)))
        
    def getPeer(self):
        """
        @return the peer's IPv6Address.

        This indicates the client's address.
        """
        return IPv6Address('TCP', *((self.client[0], self.client[1]) + ('INET',)))
        #return address.IPv4Address('TCP', *(self.client + ('INET',)))
        
class IPv6Port(tcp.Port):
    
    addressFamily = socket.AF_INET6
    transport = IPv6Server
    
    def __init__(self, port, factory, backlog=50, interface='', reactor=None):
        super(IPv6Port, self).__init__(port, factory, backlog, interface, reactor)
    
    def _buildAddr(self, addr):
        (host, port, dummy1, dummy2) = addr # are these really (host, port ?) -- check
        return IPv6Address('TCP', *(host, port))
    