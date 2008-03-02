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
    # TODO: we should definitely get these from config
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
    
    # TODO: it's complaining about lack of logging handler.
    # integrate with angel_app logger.
    from angel_app.log import getLogger
    from angel_app.config import config
    import logging
    logging.basicConfig()

    ac = config.getConfig()
    getZEOServer(ac, getFileStorage(ac))

    getLogger().growl("User", "Database (ZEO)", "Starting service on port %i." % ac.getint("zeo","listenPort"))
    import ThreadedAsync.LoopCallback
    ThreadedAsync.LoopCallback.loop()

if __name__ == "__main__":
    main()