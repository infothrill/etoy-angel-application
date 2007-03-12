"""
Module for Mac OS X specific methods
"""

import wx

APPLESCRIPT_PATH="../angel_app/wx/platform/mac/applescript/" # TODO: path (relevant for packaging)

# TODO: review command line args (whitespaces ,special chars)

import os.path as path

def showRepositoryInFilemanager(interface, port):
    script = path.join(APPLESCRIPT_PATH, "mount_repository.applescript")
    wx.Execute("/usr/bin/osascript %s '%s' '%s'" %( script, interface, str(port)), wx.EXEC_ASYNC)

def showURLInBrowser(url):
    wx.Execute("open '%s'" % url)