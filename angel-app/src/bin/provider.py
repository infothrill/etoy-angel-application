"""
DAV server that runs on the 'external' interface -- i.e. the 
communicates with other angel-app instances.
This guy is NOT safe and MUST NOT gain access to the secret key(s). 
I.e. it may NOT commit data to the angel-app (except e.g. new clone
metadata).
"""



from config.common import rootDir
from config.external import port


from angel_app.angelFile.external import External
root = External(rootDir)


from twisted.web2 import server
from twisted.web2 import channel
from twisted.internet import reactor
site = server.Site(root)
reactor.listenTCP(port, channel.HTTPFactory(site), 50)
reactor.run()
