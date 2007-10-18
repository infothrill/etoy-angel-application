"""
Module to wrap OS specific GUI functionality.
Currently this module provides these cross-platform methods:

showRepositoryInFilemanager(hostname, portnumber)
showURLInBrowser(url)
getResourcePath()

"""
from twisted.python.runtime import platform

def isMacOSX():
    return platform.isMacOSX()

def isWindows():
    return platform.isWindows()

""" Do all sorts of imports, so the methods are properly wrapped"""

# common code for all platforms:
from angel_app.gui.compat.common import getResourcePath

# platform specific code:
if isMacOSX():
    from angel_app.gui.compat.macosx import showRepositoryInFilemanager
    from angel_app.gui.compat.macosx import showURLInBrowser
elif isWindows():
    from angel_app.gui.compat.win32 import showRepositoryInFilemanager
    from angel_app.gui.compat.win32 import showURLInBrowser
else: # assuming unix/linux
    from angel_app.gui.compat.unix import showRepositoryInFilemanager
    from angel_app.gui.compat.unix import showURLInBrowser

