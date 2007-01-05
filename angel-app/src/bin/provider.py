"""
DAV server that runs on the 'external' interface -- i.e. the 
communicates with other angel-app instances.
This guy is NOT safe and MUST NOT gain access to the secret key(s). 
I.e. it may NOT commit data to the angel-app (except e.g. new clone
metadata).
"""


from angel_app.config import config
AngelConfig = config.Config()
providerport = AngelConfig.getint("provider","listenPort")
providerinterface = AngelConfig.get("provider","listenInterface")
repository = AngelConfig.get("common","repository")


from angel_app.resource.local.external.resource import External
root = External(repository)


from twisted.web2 import server
from twisted.web2 import channel
from twisted.internet import reactor
site = server.Site(root)
reactor.listenTCP(providerport, channel.HTTPFactory(site), 50, providerinterface)
print "Listening on IP", providerinterface, "port", providerport, "and serving content from", repository
reactor.run()
