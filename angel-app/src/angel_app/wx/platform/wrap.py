"""
Module to wrap some functionality that is OS specific and hide away platform details
"""
from twisted.python.runtime import platform

# TODO: add linux support

if platform.isMacOSX():
    from angel_app.wx.platform.macosx import showRepositoryInFilemanager
    from angel_app.wx.platform.macosx import showURLInBrowser


def isMacOSX():
    return platform.isMacOSX()

