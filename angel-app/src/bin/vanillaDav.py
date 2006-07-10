#from twisted.web2.dav import static
from twisted.web2 import server
from twisted.web2 import channel
from twisted.internet import reactor

from twisted.web2.dav import static

port = 9999
rootDir = "/Users/vincent/Desktop/test"
root = static.DAVFile(rootDir)
interface = "127.0.0.1"


site = server.Site(root)
reactor.listenTCP(port, channel.HTTPFactory(site), 50, interface)
reactor.run()
