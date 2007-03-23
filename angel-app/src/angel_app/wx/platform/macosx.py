"""
Module for Mac OS X specific methods
"""

import wx
import os
import common

APPLESCRIPT_PATH=os.path.join(common.getResourcePath(), "applescript")

# TODO: review command line args (whitespaces ,special chars)

def showRepositoryInFilemanager(interface, port):
    script = os.path.join(APPLESCRIPT_PATH, "mount_repository.applescript")
    wx.Execute("/usr/bin/osascript %s '%s' '%s'" %( script, interface, str(port)), wx.EXEC_ASYNC)

def showURLInBrowser(url):
    wx.Execute("open '%s'" % url)