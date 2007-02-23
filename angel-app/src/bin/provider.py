"""
DAV server that runs on the 'external' interface -- i.e. the 
communicates with other angel-app instances.
This guy is NOT safe and MUST NOT gain access to the secret key(s). 
I.e. it may NOT commit data to the angel-app (except e.g. new clone
metadata).
"""

from optparse import OptionParser
from angel_app.log import getLogger

def bootInit():
	"""
	Method to be called in __main__ before anything else. This method cannot rely on any
	framework being initialised, e.g. no logging, no exception catching etc.
	"""
	import angel_app.config.defaults
	angel_app.config.defaults.appname = "provider"

def runServer():
	from angel_app.config import config
	AngelConfig = config.getConfig()
	providerport = AngelConfig.getint("provider","listenPort")
	repository = AngelConfig.get("common","repository")

	from angel_app.resource.local.external.resource import External
	root = External(repository)

	from twisted.web2 import server
	from twisted.web2 import channel
	from twisted.internet import reactor
	site = server.Site(root)
	reactor.listenTCP(providerport, channel.HTTPFactory(site), 50)
	getLogger().info("Listening on port %d and serving content from %s", providerport, repository)
	reactor.run()

if __name__ == "__main__":
	bootInit()
	parser = OptionParser()
	parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
	parser.add_option("-l", "--log", dest="networklogging", help="use network logging?",action="store_true" ,default=False)
	(options, args) = parser.parse_args()

	import angel_app.log
	angel_app.log.setup()
	angel_app.log.enableHandler('file')
	if len(options.daemon) > 0:
		angel_app.log.enableHandler('socket')
		from angel_app import daemonizer
		daemonizer.startstop(action=options.daemon, stdout='provider.stdout', stderr='provider.stderr', pidfile='provider.pid')
	else:
		if (options.networklogging):
			angel_app.log.enableHandler('socket')
		else:
			angel_app.log.enableHandler('console')
	angel_app.log.getReady()
	runServer()
