"""
DAV server that runs on the 'internal' interface -- i.e. the UI.
This guy is safe and has access to the secret key(s). I.e. it 
may commit data to the angel-app.
"""


#from twisted.web2.dav import static
from twisted.web2 import server
from twisted.web2 import channel
from twisted.internet import reactor

#from angel_app import static
from config.common import rootDir
from config.internal import interface, port


#static.AngelFile.secretKey = loadKeysFromFile()

from angel_app.presenter.setup import setupRoot
setupRoot()

#root = static.AngelFile(rootDir)
from angel_app.angelFile.crypto import Crypto
root = Crypto(rootDir)
site = server.Site(root)
reactor.listenTCP(port, channel.HTTPFactory(site), 50, interface)
reactor.run()
