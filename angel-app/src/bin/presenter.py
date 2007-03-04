"""
DAV server that runs on the 'internal' interface -- i.e. the UI.
This guy is safe and has access to the secret key(s). I.e. it 
may commit data to the angel-app.
"""

from optparse import OptionParser
from angel_app.log import getLogger

def bootInit():
    """
    Method to be called in __main__ before anything else. This method cannot rely on any
    framework being initialised, e.g. no logging, no exception catching etc.
    """
    import angel_app.config.globals
    angel_app.config.globals.appname = "presenter"
    
    # TODO: ugly twisted workaround to provide angel_app xml elements
    from twisted.web2.dav.element import parser
    from angel_app import elements
    parser.registerElements(elements)

def postConfigInit():
    """
    Run this method after the config system is initialized.
    """
    from angel_app.admin.directories import makeDirectories
    makeDirectories()

    # setup our internal temporary path for files:
    from angel_app import singlefiletransaction
    singlefiletransaction.setup()

def runServer():
    from angel_app.config import config
    AngelConfig = config.getConfig()
    port = AngelConfig.getint("presenter","listenPort")
    interface = AngelConfig.get("presenter","listenInterface")
    repository = AngelConfig.get("common","repository")

    #from angel_app.server.internal.setup import setupRoot
    #setupRoot()

    from angel_app.resource.local.internal.resource import Crypto
    Crypto.rootDirectory = repository
    root = Crypto(repository)

    from twisted.web2 import server
    from twisted.web2 import channel
    from twisted.internet import reactor
    site = server.Site(root)
    reactor.listenTCP(port, channel.HTTPFactory(site), 50, interface)
    getLogger().info('Listening on IP %s port %d and serving content from %s', interface, port, repository)
    reactor.run()


def main():
    bootInit()
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
    parser.add_option("-l", "--log", dest="networklogging", help="use network logging?",action="store_true" ,default=False)
    (options, args) = parser.parse_args()

    # setup/configure config system
    from angel_app.config.config import getConfig
    angelConfig = getConfig(options.config)
    postConfigInit()
    angelConfig.bootstrapping = False

    # setup/configure logging
    import angel_app.log
    angel_app.log.setup()
    angel_app.log.enableHandler('file')
    if len(options.daemon) > 0:
        angel_app.log.enableHandler('socket')
        from angel_app import daemonizer
        daemonizer.startstop(action=options.daemon, stdout='presenter.stdout', stderr='presenter.stderr', pidfile='presenter.pid')
    else:
        if (options.networklogging):
            angel_app.log.enableHandler('socket')
        else:
            angel_app.log.enableHandler('console')
    angel_app.log.getReady()
    runServer()

if __name__ == "__main__":
    main()