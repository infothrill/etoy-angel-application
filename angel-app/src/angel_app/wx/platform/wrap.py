"""
Module to wrap OS specific GUI functionality.
Currently this module provides these cross-platform methods:

showRepositoryInFilemanager(hostname, portnumber)
showURLInBrowser(url)

"""
from twisted.python.runtime import platform

# TODO: add linux support

if platform.isMacOSX():
    from angel_app.wx.platform.macosx import showRepositoryInFilemanager
    from angel_app.wx.platform.macosx import showURLInBrowser
elif platform.isWindows():
    from angel_app.wx.platform.win32 import showRepositoryInFilemanager
    from angel_app.wx.platform.win32 import showURLInBrowser
else: # assuming unix/linux
    from angel_app.wx.platform.unix import showRepositoryInFilemanager
    from angel_app.wx.platform.unix import showURLInBrowser

def isMacOSX():
    return platform.isMacOSX()

