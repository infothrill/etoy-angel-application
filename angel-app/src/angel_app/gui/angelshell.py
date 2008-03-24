
import wx
import wx.py as py

from angel_app.config.config import getConfig


# executed by angelshell if no angelshellinit.py is found:
defaultShellCommands = [
              "from angel_app.config.config import getConfig",
              "cc = getConfig()",
              "rootPath = cc.get('common', 'repository')",
              "from angel_app.resource.local.internal.resource import Crypto",
              "root = Crypto(rootPath)"
              ]


class AngelShellWindow(wx.Frame):
    """
    a frame containing an interactive python shell as returned by angelshell()  
    """
    def __init__(self, parent, id, title, size = None):
        wx.Frame.__init__(self, parent, id, title, size=(500, 300))
        self.Statusbar = self.CreateStatusBar(1, 0)
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add(angelshell(parent = self), proportion = 2, flag=wx.ALL|wx.EXPAND, border = 1)
        self.SetSizer(Sizer)
        self.CentreOnParent()
        self.Show(True)

def angelshell(parent):
    """
    return a wxwidget with an interactive python shell (has no enclosing window or panel)
    """
    # sort of a joke for now ;-)
    def getInitCommands():
        try:
            fileName = getConfig().get("gui", "angelshellinit")
            return open(fileName).readlines()
        except IOError: # file not found
            return defaultShellCommands
    
    onShellLoad = getInitCommands()
    intro = 'ANGELSHELL %s - EVERYTHING YOU NEED FOR BACKUP' % py.version.VERSION
    win = py.shell.Shell(parent, -1, introText=intro)
    for command in onShellLoad:
        win.Execute(command)
    return win

