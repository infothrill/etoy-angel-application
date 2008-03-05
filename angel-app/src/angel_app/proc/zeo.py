def getFileStorage(angelConfig):
    """
    @param angelConfig -- an angel-app configuration instance
    """
    from ZODB.config import FileStorage # That's a FileStorage *opener*!
    class FSConfig:
        def __init__(self, name, path):
            self._name = name
            self.path = path
            self.create = 0
            self.read_only = 0
            self.stop = None
            self.quota = None
        def getSectionName(self):
            return self._name
    # From StorageServer constructor docs:
    # By convention, storage names are typically
    # strings representing small integers starting at '1'.
    UNIQUE_NAME_FOR_STORAGE = '1' 
    DATA_BASE_FILE = angelConfig.get("zeo", "zodbfs")
    opener = FileStorage(
                       FSConfig(
                                UNIQUE_NAME_FOR_STORAGE, 
                                DATA_BASE_FILE))
    return {UNIQUE_NAME_FOR_STORAGE : opener.open()}

def getZEOServer(angelConfig, storage):
    """
    @param angelConfig -- an angel-app configuration instance
    @param storage -- a ZEO FileStorage instance as returned by getFileStorage
    """
    listenAddress = (
                     "127.0.0.1", 
                     angelConfig.getint("zeo","listenPort")
                     )
    
    from ZEO.StorageServer import StorageServer
    return StorageServer(listenAddress, storage)

def main(args=None):
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-d", "--daemon", dest="daemon", help="daemon mode?", default='')
    parser.add_option("-c", "--config", dest="config", help="alternative config file", default=None)
    parser.add_option("-l", "--log", dest="networklogging", help="use network logging?", action="store_true" , default=False)
    (options, dummyargs) = parser.parse_args()
    
    from angel_app.config.config import getConfig
    angelConfig = getConfig(options.config)

    angelConfig.bootstrapping = False

    appname = 'zeo'
    from angel_app.log import initializeLogging
    loghandlers = ['file'] # always log to file
    if len(options.daemon) > 0:
        loghandlers.append('socket')
    else:
        if (options.networklogging):
            loghandlers.append('socket')
        else:
            loghandlers.append('console')
            loghandlers.append('growl')

    initializeLogging(appname, loghandlers)
    from angel_app.log import getLogger

    if len(options.daemon) > 0:
        from angel_app.proc import daemonizer
        daemonizer.startstop(action=options.daemon, stdout=appname+'.stdout', stderr=appname+'.stderr', pidfile=appname+'.pid')

    getZEOServer(angelConfig, getFileStorage(angelConfig))

    getLogger().growl("User", "STARDUST COLLECTOR", "Starting service on port %i." % angelConfig.getint("zeo","listenPort"))
    import ThreadedAsync.LoopCallback
    ThreadedAsync.LoopCallback.loop()

if __name__ == "__main__":
    main()