#from twisted.web2.dav import static
from twisted.web2 import server
from twisted.web2 import channel
from twisted.internet import reactor

from angel_app.davServer import static

port = 9998
rootDir = "/Users/vincent/Desktop/test"
root = static.AngelFile(rootDir)
interface = "127.0.0.1"


site = server.Site(root)
reactor.listenTCP(port, channel.HTTPFactory(site), 50, interface)
reactor.run()
