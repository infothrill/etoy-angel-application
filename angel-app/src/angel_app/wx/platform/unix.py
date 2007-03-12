
#for (int count = 0; count < browsers.length && browser == null; count++)
#if (Runtime.getRuntime().exec(new String[] {"which", browsers[count]}).waitFor() == 0) browser = browsers[count]; 
#if (browser == null) throw new Exception("Could not find web browser"); else Runtime.getRuntime().exec(new String[] {browser, url}); } }
#catch (Exception e) { JOptionPane.showMessageDialog(null, errMsg + ":\n" + e.getLocalizedMessage()); } } }


"""
Module for Unix/Linux specific methods
"""

import wx

# TODO: review command line args (whitespaces ,special chars)

import os, sys

def _which (filename):
    """
    emulates the `which` command line tool
    """
    if not os.environ.has_key('PATH') or os.environ['PATH'] == '':
        p = os.defpath
    else:
        p = os.environ['PATH']

    pathlist = p.split (os.pathsep)

    for path in pathlist:
        f = os.path.join(path, filename)
        if os.access(f, os.X_OK):
            return f
    return None

def _findWebBrowser():
    # list of possible browser, in order of preference:
    possibleBrowsers = [ "x-www-browser", "mozilla-firefox", "firefox", "iceweasel", "konqueror", "epiphany", "mozilla", "netscape", "opera"]
    for p in possibleBrowsers:
        browser = _which(p)
        if not browser == None:
            return browser
    return None

def showRepositoryInFilemanager(interface, port):
    wx.Execute("start http://%s:%s" %( interface, str(port)), wx.EXEC_ASYNC)

def showURLInBrowser(url):
    browser = _findWebBrowser()
    if browser == None:
        return # TODO : alert user that no web-browser was found!
    wx.Execute("%s '%s'" % (browser, url))

