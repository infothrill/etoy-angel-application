"""
A module providing an interactive python shell in wx
"""

import wx
import wx.py as py

_ = wx.GetTranslation

from angel_app.config.config import getConfig
from angel_app.log import getLogger

log = getLogger(__name__)

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
        self.shellpanel = angelshell(parent = self) 
        self.shellpanel.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        Sizer.Add(self.shellpanel, proportion = 2, flag=wx.ALL|wx.EXPAND, border = 1)
        self.SetSizer(Sizer)
        self.CentreOnParent()
        self.Show(True)

    def OnKeyDown(self, event):
        """
        catch and handle a couple of special keys like Cmd-C or Esc
        
        @param event: wx.KeyEvent
        """
        keycode = event.GetKeyCode()
        log.debug("OnKeyDown() got keycode: %s" % keycode)
        if keycode == wx.WXK_ESCAPE:
            ret  = wx.MessageBox(_('Quit the shell?'), _('Question'), wx.YES_NO | wx.CENTRE | wx.NO_DEFAULT, self)
            if ret == wx.YES:
                self.Close()
        elif event.CmdDown(): # Cmd or Ctrl
            if keycode == 67: # 'c'
                self.shellpanel.Copy()
            if keycode == 87: # 'w'
                self.Close()
        event.Skip() # pass it up the hierarchy!


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

if __name__ == '__main__':
    """
    This allows us to run it separately from the rest of the GUI
    """
    from angel_app.log import initializeLogging
    initializeLogging()
    app = wx.App(0)
    app.config = getConfig()
    AngelShellWindow(None, -1, _('Angelshell'))
    app.MainLoop()