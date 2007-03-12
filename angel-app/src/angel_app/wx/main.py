import wx
import  wx.gizmos   as  gizmos

import time
import angel_app.wx.platform.wrap as platformwrap
import angel_app.wx.masterthread
from angel_app.config import config
AngelConfig = config.getConfig()

IMAGE_PATH="../../distrib/images/" # FIXME: this shall not be hardcoded (and have no os specific stuff)!
M221E_LOGO_SMALL = IMAGE_PATH+"m221elogosmall.jpg"

class AngelMainFrame(wx.Frame):
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(400, 200))
        
        # define the menus
        self.menu_bar  = wx.MenuBar()
  
        # File menu
        self.file_menu = wx.Menu()
        ID_FILE_SHOW_REPO_BROWSER = wx.NewId()
        self.file_menu.Append(ID_FILE_SHOW_REPO_BROWSER, "O&pen repository in web-browser", "Open repository in web-browser")
        self.Bind(wx.EVT_MENU, self.on_help_presenter, id=ID_FILE_SHOW_REPO_BROWSER)
        ID_FILE_SHOW_REPO_FILEMANAGER = wx.NewId()
        if platformwrap.isMacOSX():
            filemanager = "Finder"
        else:
            filemanager = "file manager"
        self.file_menu.Append(ID_FILE_SHOW_REPO_FILEMANAGER, "O&pen repository in %s" % filemanager, "Open repository in %s" % filemanager)
        self.Bind(wx.EVT_MENU, self.on_repo_in_filemanager, id=ID_FILE_SHOW_REPO_FILEMANAGER)
        self.file_menu.Append(wx.ID_EXIT, "E&xit", "Terminate the program")
        self.Bind(wx.EVT_MENU, self.doExit, id=wx.ID_EXIT)
        self.file_menu.Append(wx.ID_CLOSE, "Q&uit", "Quit")
        self.Bind(wx.EVT_MENU, self.doExit, id=wx.ID_CLOSE)
        self.menu_bar.Append(self.file_menu, "&File")

        # Help menu
        self.help_menu = wx.Menu()
        self.help_menu.Append(wx.ID_ABOUT, "&About")
        self.Bind(wx.EVT_MENU, self.on_about_request, id=wx.ID_ABOUT)
        ID_HELP_WIKI = wx.NewId()
        self.help_menu.Append(ID_HELP_WIKI, "&Angel-App Wiki (Website)")
        self.Bind(wx.EVT_MENU, self.on_help_wiki, id=ID_HELP_WIKI)
        ID_HELP_M221E = wx.NewId()
        self.help_menu.Append(ID_HELP_M221E, "&MISSION ETERNITY (Website)")
        self.Bind(wx.EVT_MENU, self.on_help_m221e, id=ID_HELP_M221E)

        ID_HELP_LICENSE = wx.NewId()
        self.help_menu.Append(ID_HELP_LICENSE, "&License")
        self.Bind(wx.EVT_MENU, self.on_help_license, id=ID_HELP_LICENSE)

        self.menu_bar.Append(self.help_menu, "&Help")
# osascript -e "try" -e "mount volume \"http://localhost:6222/\"" -e "end try"
        self.SetMenuBar(self.menu_bar)
        # end define the menus

        self.sb = AngelStatusBar(self)
        self.SetStatusBar(self.sb)
        
        self.SetBackgroundColour(wx.WHITE)
        self.bitmap = wx.Bitmap(M221E_LOGO_SMALL)
        wx.EVT_PAINT(self, self.OnPaint)
        self.static_text = wx.StaticText(self, -1, "MISSION ETERNITY's Angel-App",style=wx.ALIGN_CENTRE)

        self.Centre()


        _daemon = angel_app.wx.masterthread.MasterThread()
        _daemon.setDaemon(True)
        _daemon.start() # TODO: shall we always start master on init??
        self.daemon = _daemon

        self.Bind(wx.EVT_CLOSE, self.OnQuit)


    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 110, 20)
    
    def OnQuit(self, event):
        self.daemon.stop()
        self.Destroy()

    def doExit(self, event):
        print "Exiting on user request"
        self.Close(True)

    def on_repo_in_filemanager(self, event):
        interface = AngelConfig.get("presenter", "listenInterface")
        port = AngelConfig.get("presenter", "listenPort")
        platformwrap.showRepositoryInFilemanager(interface, port)

    def on_about_request(self, event):
        # copyright symbol: \u00A9
        dlg = wx.MessageDialog(self, u'Version pre-alpha0.1\n\u00A9 Copyright 2006-2007 etoy.VENTURE ASSOCIATION,\nall rights reserved', # TODO embed version string
                               'Angel-App',
                               wx.OK | wx.ICON_INFORMATION
                               )
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()
        
    def on_help_license(self, event):
        text = """Copyright (c) 2006-2007, etoy.VENTURE ASSOCIATION
All rights reserved.
         
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
*  Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
*  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
*  Neither the name of etoy.CORPORATION nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
         
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
""" 
        from wx.lib.dialogs import ScrolledMessageDialog
        dlg = ScrolledMessageDialog(self, text, 'Angel-App License Information')
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()

    def on_help_presenter(self, event):
        interface = AngelConfig.get("presenter", "listenInterface")
        port = AngelConfig.get("presenter", "listenPort")
        platformwrap.showURLInBrowser("http://%s:%s"% (interface, port))

    def on_help_wiki(self, event):
        platformwrap.showURLInBrowser("http://angelapp.missioneternity.org")
    
    def on_help_m221e(self, event):
        platformwrap.showURLInBrowser("http://www.missioneternity.org")
    

class AngelStatusBar(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)

        # This status bar has one field
        self.SetFieldsCount(1)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-2])

        # We're going to use a timer to drive a 'clock' in the last
        # field.
        self.timer = wx.PyTimer(self.Notify)
        self.timer.Start(1000)
        self.Notify()

    # Handles events from the timer we started in __init__().
    # We're using it to drive a 'clock' in field 0
    def Notify(self):
        t = time.localtime(time.time())
        st = time.strftime("%d-%b-%Y   %H:%M:%S", t)
        self.SetStatusText(st, 0)


class AngelApp(wx.App):
    def OnInit(self):
        mainframe = AngelMainFrame(None, -1, "Angel-App: CROSSING THE DEAD-LINE")
        mainframe.Show(True)
        self.SetTopWindow(mainframe)
        return True

    #def onExit(self, event):
    #    self.mainframe.daemon.stop()

if __name__ == '__main__':
    pass