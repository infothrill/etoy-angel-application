import wx

import angel_app.wx.masterthread
from angel_app.wx.splash import AngelSplashScreen

IMAGE_PATH="../../distrib/images/" # FIXME: this shall not be hardcoded (and have no os specific stuff)!
M221E_LOGO_SMALL = IMAGE_PATH+"m221elogosmall.jpg"

class AngelMainFrame(wx.Frame):
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(450, 200))
        
        # define the menus
        self.menu_bar  = wx.MenuBar()
  
        self.file_menu = wx.Menu()
        self.file_menu.Append(wx.ID_EXIT, "E&xit", "Terminate the program")
        self.Bind(wx.EVT_MENU, self.doExit, id=wx.ID_EXIT)
        self.file_menu.Append(wx.ID_CLOSE, "Q&uit", "Quit")
        self.Bind(wx.EVT_MENU, self.doExit, id=wx.ID_CLOSE)
        self.menu_bar.Append(self.file_menu, "&File")

        self.help_menu = wx.Menu()
        self.help_menu.Append(wx.ID_ABOUT, "&About")
        self.Bind(wx.EVT_MENU, self.on_about_request, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self.on_about_request, id=wx.ID_ABOUT)
        ID_HELP_WIKI = wx.NewId()
        self.help_menu.Append(ID_HELP_WIKI, "&Angel-App Wiki (Website)")
        self.Bind(wx.EVT_MENU, self.on_help_wiki, id=ID_HELP_WIKI)

        ID_HELP_M221E = wx.NewId()
        self.help_menu.Append(ID_HELP_M221E, "&MISSION ETERNITY (Website)")
        self.Bind(wx.EVT_MENU, self.on_help_m221e, id=ID_HELP_M221E)

        self.menu_bar.Append(self.help_menu, "&Help")
        self.SetMenuBar(self.menu_bar)
        # end define the menus

        self.SetBackgroundColour(wx.WHITE)
        self.bitmap = wx.Bitmap(M221E_LOGO_SMALL)
        wx.EVT_PAINT(self, self.OnPaint)
        self.Centre()
        self.static_text = wx.StaticText(self, -1, "MISSION ETERNITY's Angel-App",style=wx.ALIGN_CENTRE)

        _daemon = angel_app.wx.masterthread.MasterThread()
        _daemon.setDaemon(True)
        _daemon.start() # TODO: shall we always start master on init??
        self.daemon = _daemon

        self.Bind(wx.EVT_CLOSE, self.OnQuit)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bitmap, 60, 20)
    
    def OnQuit(self, event):
        self.daemon.stop()
        self.Destroy()

    def doExit(self, event):
        print "closing"
        self.Close(True)
        
    def on_about_request(self, event):
        text = """Copyright (c) 2006-2007, etoy.VENTURE ASSOCIATION
All rights reserved.
         
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
*  Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
*  Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
*  Neither the name of etoy.CORPORATION nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
         
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
""" 
        from wxPython.lib.dialogs import wxScrolledMessageDialog # TODO:  DeprecationWarning: The wxPython compatibility package is no longer automatically generated or activly maintained.  Please switch to the wx package as soon as possible. from wxPython.lib.dialogs import wxScrolledMessageDialog
        dlg = wxScrolledMessageDialog(self, text, 'About Angel-App')
        dlg.ShowModal()

    def on_help_wiki(self, event):
        wx.Execute("open http://angelapp.missioneternity.org") # FIXME: only works on OS X
    
    def on_help_m221e(self, event):
        wx.Execute("open http://www.missioneternity.org") # FIXME: only works on OS X
    



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