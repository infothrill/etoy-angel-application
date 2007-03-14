"""
The main GUI module.
"""

import wx

import time
import angel_app.wx.platform.wrap as platformwrap
import angel_app.wx.masterthread
from angel_app.config import config
AngelConfig = config.getConfig()
import os.path as path

IMAGE_PATH="../../distrib/images/" # TODO: path shall not be hardcoded (relevant for packaging)
M221E_LOGO_SMALL = path.join(IMAGE_PATH, "m221elogosmall.jpg")

class AngelMainFrame(wx.Frame):
    def __init__(self, parent, ID, title):
        """
        The constructor, initializes the menus, the mainframe with the logo and the statusbar.
        By default, also starts the p2p process automatically on start-up
        """
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(340, 150))
        
        # define the menus
        self.menu_bar  = wx.MenuBar()
  
        # TODO: add File->Import secret key...
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

        # network menu
        self.net_menu = wx.Menu()
        ID_NET_START = wx.NewId()
        self.net_menu.Append(ID_NET_START, "S&tart p2p service", "Start p2p service")
        self.Bind(wx.EVT_MENU, self.on_net_start, id=ID_NET_START)

        ID_NET_STOP = wx.NewId()
        self.net_menu.Append(ID_NET_STOP, "S&top p2p service", "Stop p2p service")
        self.Bind(wx.EVT_MENU, self.on_net_stop, id=ID_NET_STOP)
        self.menu_bar.Append(self.net_menu, "&Network")

        # Help menu
        self.help_menu = wx.Menu()
        self.help_menu.Append(wx.ID_ABOUT, "A&bout", "About Angel-App")
        self.Bind(wx.EVT_MENU, self.on_about_request, id=wx.ID_ABOUT)
        ID_HELP_WIKI = wx.NewId()
        self.help_menu.Append(ID_HELP_WIKI, "Angel-App W&iki (Website)", "http://angelapp.missioneternity.org")
        self.Bind(wx.EVT_MENU, self.on_help_wiki, id=ID_HELP_WIKI)
        ID_HELP_M221E = wx.NewId()
        self.help_menu.Append(ID_HELP_M221E, "M&ISSION ETERNITY (Website)", "http://www.missioneternity.org")
        self.Bind(wx.EVT_MENU, self.on_help_m221e, id=ID_HELP_M221E)

        ID_HELP_LICENSE = wx.NewId()
        self.help_menu.Append(ID_HELP_LICENSE, "S&oftware License", "Software License")
        self.Bind(wx.EVT_MENU, self.on_help_license, id=ID_HELP_LICENSE)

        self.menu_bar.Append(self.help_menu, "&Help")

        self.SetMenuBar(self.menu_bar)
        # end define the menus

        self.SetBackgroundColour(wx.WHITE)
        self.bitmap = wx.Bitmap(M221E_LOGO_SMALL)
        wx.EVT_PAINT(self, self.OnPaint)
        self.static_text = wx.StaticText(self, -1, "MISSION ETERNITY's Angel-App",style=wx.ALIGN_CENTRE)

        self.Centre()

        _daemon = angel_app.wx.masterthread.MasterThread()
        _daemon.setDaemon(True)
        _daemon.start() # TODO: shall we always start master on init??
        self.daemon = _daemon

        self.sb = AngelStatusBar(self, self.daemon)
        self.SetStatusBar(self.sb)

        self.Bind(wx.EVT_CLOSE, self.OnQuit)


    def OnPaint(self, event):
        """
        Handler for wx.EVT_PAINT event.
        Also draws the m221e logo.
        """
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 90, 20)
    
    def OnQuit(self, event):
        """
        Handler for wx.EVT_CLOSE event
        """
        self.daemon.stop()
        self.Destroy()

    def doExit(self, event):
        """
        Exits the application explicitly
        """
        print "Exiting on user request"
        self.Close(True)

    def on_net_start(self, event):
        """
        Starts the p2p process if not running
        """
        if not self.daemon.isAlive():
            self.daemon.run()

    def on_net_stop(self, event):
        """
        Stops the p2p process if running
        """
        if self.daemon.isAlive():
            self.daemon.stop()
    
    def on_repo_in_filemanager(self, event):
        """
        Opens the local private repository from presenter in the
        file manager
        """
        interface = AngelConfig.get("presenter", "listenInterface")
        port = AngelConfig.get("presenter", "listenPort")
        platformwrap.showRepositoryInFilemanager(interface, port)

    def on_about_request(self, event):
        """
        Shows a dialogue with an icon, version and copyright
        """
        # copyright symbol: \u00A9
        dlg = wx.MessageDialog(self, u'Version pre-alpha0.1\n\u00A9 Copyright 2006-2007 etoy.VENTURE ASSOCIATION,\nall rights reserved', # TODO embed version string
                               'Angel-App',
                               wx.OK | wx.ICON_INFORMATION
                               )
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()
        
    def on_help_license(self, event):
        """
        Shows the license in a scroll box
        """
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
        """
        Opens the local presenter website in a web browser
        """
        interface = AngelConfig.get("presenter", "listenInterface")
        port = AngelConfig.get("presenter", "listenPort")
        platformwrap.showURLInBrowser("http://%s:%s"% (interface, port))

    def on_help_wiki(self, event):
        """
        Opens http://angel-app.missioneternity.org in a web browser
        """
        platformwrap.showURLInBrowser("http://angelapp.missioneternity.org")
    
    def on_help_m221e(self, event):
        """
        Opens http://www.missioneternity.org in a web browser
        """
        platformwrap.showURLInBrowser("http://www.missioneternity.org")
    

class AngelStatusBar(wx.StatusBar):
    """
    Status bar for the main frame. Shows 2 things:
    - currently selected menu
    - p2p status (running/stopped)
    """
    def __init__(self, parent, masterproc):
        """
        Constructor, takes an additional parameter pointing to the
        thread object runing the p2p process. Initializes a timer to
        see if the p2p process is running.
        """
        self.masterproc = masterproc
        wx.StatusBar.__init__(self, parent, -1)

        # This status bar has one field
        self.SetFieldsCount(2)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-2,-1])

        # We're going to use a timer to drive a 'clock' in the last
        # field.
        self.timer = wx.PyTimer(self.Notify)
        self.timer.Start(1000)
        self.Notify()

    def Notify(self):
        """
        Timer callback to check if the p2p process is running and
        set the status bar text accordingly.
        """
        if self.masterproc.isAlive():
            status = "p2p running"
        else:
            status = "p2p stopped"
        self.SetStatusText(status, 1)


class AngelApp(wx.App):
    """
    The main wx.App
    """
    def OnInit(self):
        """
        Instantiates the main frame and shows it
        """
        mainframe = AngelMainFrame(None, -1, "Angel-App: CROSSING THE DEAD-LINE")
        mainframe.Show(True)
        self.SetTopWindow(mainframe)
        return True

if __name__ == '__main__':
    pass