"""
Module for Windows specific methods
"""

import wx

# TODO: review command line args (whitespaces ,special chars)

import os.path as path

def showRepositoryInFilemanager(interface, port):
    wx.Execute("start http://%s:%s" %( interface, str(port)), wx.EXEC_ASYNC)

def showURLInBrowser(url):
    wx.Execute("start '%s'" % url)