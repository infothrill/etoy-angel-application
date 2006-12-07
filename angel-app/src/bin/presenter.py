"""
DAV server that runs on the 'internal' interface -- i.e. the UI.
This guy is safe and has access to the secret key(s). I.e. it 
may commit data to the angel-app.
"""

from twisted.web2 import server
from twisted.web2 import channel
from twisted.internet import reactor

#from angel_app import static
from angel_app.config import config
AngelConfig = config.Config()
port = AngelConfig.getint("presenter","listenPort")
interface = AngelConfig.get("presenter","listenInterface")
repository = AngelConfig.get("common","repository")

from angel_app.server.internal.setup import setupRoot
setupRoot()

from angel_app.resource.local.internal.resource import Crypto
Crypto.rootDirectory = repository
root = Crypto(repository)

site = server.Site(root)
reactor.listenTCP(port, channel.HTTPFactory(site), 50, interface)
print "Listening on IP", interface, "port", port, "and serving content from", repository
reactor.run()
