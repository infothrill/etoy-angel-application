"""
DAV server that runs on the 'external' interface -- i.e. the 
communicates with other angel-app instances.
This guy is NOT safe and MUST NOT gain access to the secret key(s). 
I.e. it may NOT commit data to the angel-app (except e.g. new clone
metadata).
"""


#from twisted.web2.dav import static
from twisted.web2 import server
from twisted.web2 import channel
from twisted.internet import reactor

from angel_app import static

port = 9999
rootDir = "/Users/vincent/Desktop/test"
root = static.AngelFile(rootDir)
interface = "localhost"


site = server.Site(root)
reactor.listenTCP(port, channel.HTTPFactory(site), 50, interface)
reactor.run()
