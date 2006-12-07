"""
DAV server that runs on the 'external' interface -- i.e. the 
communicates with other angel-app instances.
This guy is NOT safe and MUST NOT gain access to the secret key(s). 
I.e. it may NOT commit data to the angel-app (except e.g. new clone
metadata).
"""



from angel_app.config import common, external


from angel_app.resource.local.external.resource import External
root = External(common.rootDir)


from twisted.web2 import server
from twisted.web2 import channel
from twisted.internet import reactor
site = server.Site(root)
reactor.listenTCP(external.port, channel.HTTPFactory(site), 50)
reactor.run()
