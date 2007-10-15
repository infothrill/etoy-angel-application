def bootInit():
    """
    Method to be called in __main__ before anything else. This method cannot rely on any
    framework being initialised, e.g. no logging, no exception catching etc.
    """    
    pass
    
    
def postConfigInit():
    """
    Run this method after the config system is initialized.
    """
    from angel_app.admin.directories import makeDirectories
    makeDirectories()

    # setup our internal temporary path for files:
    from angel_app import singlefiletransaction
    singlefiletransaction.setup()


def boot():
    bootInit()
    # setup/configure config system
    from angel_app.config.config import getConfig
    angelConfig = getConfig()
    postConfigInit()
    angelConfig.bootstrapping = False

    appname = "gui"
    # setup/configure logging
    from angel_app.log import initializeLogging
    loghandlers = ['file', 'console'] # always log to file
    initializeLogging(appname, loghandlers)

    return True

def dance(options):
    import angel_app.wx.main
    app = angel_app.wx.main.AngelApp(0)
    app.MainLoop()


if __name__ == '__main__':
    options = boot()
    dance(options)