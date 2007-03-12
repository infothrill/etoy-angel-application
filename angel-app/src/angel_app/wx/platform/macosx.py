import wx

# FIXME: review command line args (whitespaces ,special chars)

def showRepositoryInFilemanager(interface, port):
    osascript = "../angel_app/wx/platform/mac/applescript/mount_repository.applescript" # FIXME: paths!!
    wx.Execute("osascript %s %s %s" %( osascript, interface, port))

def showURLInBrowser(url):
    wx.Execute("open %s" % url)