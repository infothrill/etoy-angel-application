def getFileStorage():
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
    DATA_BASE_FILE = "/Users/vincent/foo.fs"
    opener = FileStorage(
                       FSConfig(
                                UNIQUE_NAME_FOR_STORAGE, 
                                DATA_BASE_FILE))
    return {UNIQUE_NAME_FOR_STORAGE : opener.open()}

def getZEOServer(storage):
    from ZEO.StorageServer import StorageServer
    
    # TODO: we should get this from config
    address = ("127.0.0.1", 6223)
    return StorageServer(address, storage)

def main(args=None):
    
    # TODO: it's complaining about lack of logging handler.
    # integrate with angel_app logger.
    from angel_app.log import getLogger
    from angel_app.config import config
    import logging
    logging.basicConfig()
    getZEOServer(getFileStorage())

    getLogger().growl("User", "Database", "Starting service.")
    import ThreadedAsync.LoopCallback
    ThreadedAsync.LoopCallback.loop()

if __name__ == "__main__":
    main()