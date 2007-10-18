import os

import wx
import wx.html

import angel_app.wx.compat.wrap as platformwrap
from angel_app.version import getVersionString
from angel_app.version import getBuildString
from angel_app.version import getPythonVersionString

_ = wx.GetTranslation

class AboutWindow(wx.Dialog):
    """Information window"""

    def __init__(self, parent, id, title, pos=wx.DefaultPosition, 
                size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)

        hboxButtons = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)

        bmp = wx.Bitmap(os.path.join(platformwrap.getResourcePath(), "images", "m221elogosmall.jpg"), wx.BITMAP_TYPE_JPEG)
        vbox.Add(wx.StaticBitmap(self, -1, bmp, wx.Point(-1, -1)), 0, wx.ALL | wx.CENTRE, 5)

        name = "ANGEL APPLICATION"
        version = 'version %s build (%s)' % (getVersionString(), getBuildString())
        title = "%s %s" % (name, version)
        website = "http://angelapp.missioneternity.org/"
        description ="""The ANGEL APPLICATION (a subproject of MISSION ETERNITY) aims to minimize,
and ideally eliminate, the administrative and material costs of backing up.
It does so by providing a peer-to-peer/social storage infrastructure where
people collaborate to back up each other's data."""

        # unicode copyright symbol: \u00A9
        copyright = u'\u00A9 Copyright 2006-2007 etoy.VENTURE ASSOCIATION, all rights reserved.'

        titleLabel = wx.StaticText(self, -1, title, 
                                style=wx.ALIGN_CENTER)
        titleLabel.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD))
        vbox.Add(titleLabel, 1, wx.ALL | wx.ALIGN_CENTER, 5)

        copyLabel = wx.StaticText(self, -1, copyright, style=wx.ALIGN_CENTER)
        copyLabel.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        vbox.Add(copyLabel, 1, wx.ALL | wx.ALIGN_CENTER, 5)

        descLabel = wx.StaticText(self, -1,  _(description), style=wx.ALIGN_CENTER)
        descLabel.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
        vbox.Add(descLabel, 1, wx.ALL | wx.ALIGN_CENTER, 5)

        pageLabel = wx.HyperlinkCtrl(self, -1, website, website, wx.DefaultPosition)
        pageLabel.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
        vbox.Add(pageLabel, 1, wx.ALL | wx.ALIGN_CENTER, 5)

        vbox.Add(wx.StaticLine(self, -1), 0, wx.ALL | wx.EXPAND, 5)

        self.buttonCredits = wx.Button(self, 2004, _("C&redits"))
        hboxButtons.Add(self.buttonCredits, 0, wx.ALL | wx.ALIGN_LEFT, 3)
      
        self.buttonLicence = wx.Button(self, 2006, _("&Licence"))
        hboxButtons.Add(self.buttonLicence, 0, wx.ALL | wx.ALIGN_LEFT, 3)
      
        self.buttonOK = wx.Button(self, 2003, _("&Close"))
        hboxButtons.Add(self.buttonOK, 0, wx.ALL | wx.ALIGN_RIGHT, 3)
      
        vbox.Add(hboxButtons, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        self.SetSizer(vbox)
        vbox.Fit(self)

        wx.EVT_BUTTON(self, 2003, self.onClose)
        wx.EVT_BUTTON(self, 2004, self.onCredits)
        wx.EVT_BUTTON(self, 2006, self.onLicence)

    def onClose(self, event):
        self.Destroy()

    def onCredits(self, event):
        creditsWindow = CreditsWindow(self, -1, _("Credits"), size=(500, 240))
        creditsWindow.CentreOnScreen()
        creditsWindow.Show()
      
    def onLicence(self, event):
        licenseWindow = LicenseWindow(self, -1, _("Licence"), size=(500, 400), style=wx.DEFAULT_FRAME_STYLE)
        licenseWindow.CenterOnScreen()
        licenseWindow.Show(True)


class LicenseWindow(wx.Frame):
    """Licence window class"""

    def __init__(self, parent, id, title, pos=wx.DefaultPosition,
                size=wx.DefaultSize, style=wx.CENTRE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        vbox = wx.BoxSizer(wx.VERTICAL)

        #
        # Read licence file
        #
        try:
            fd = open(os.path.join(platformwrap.getResourcePath(), "files", 'copying.html'))
            data = fd.read()
            fd.close()
        except Exception, e:
            print `e` # TODO
            #systemLog(ERROR, "Unable to read licence file: %s" % e)
            data = "Error: <i>licence file not found</i>"

        scWinAbout = wx.ScrolledWindow(self, -1, wx.DefaultPosition,
                                    wx.Size(-1, -1))

        htmlWin = wx.html.HtmlWindow(scWinAbout, -1, style=wx.SUNKEN_BORDER)
        htmlWin.SetFonts('Helvetica', 'Fixed', [12]*5)
        htmlWin.SetPage(data)
      
        scBox = wx.BoxSizer(wx.VERTICAL)
        scBox.Add(htmlWin, 1, wx.ALL | wx.EXPAND, 1)
        scWinAbout.SetSizer(scBox)
        vbox.Add(scWinAbout, 1, wx.ALL | wx.EXPAND, 5)

        self.buttonClose = wx.Button(self, 2002, _("&Close"))
        vbox.Add(self.buttonClose, 0, wx.ALL | wx.ALIGN_RIGHT, 5)

        self.SetSizer(vbox)

        wx.EVT_BUTTON(self, 2002, self.onClose)


    def onClose(self, event):
        """This method is invoked when Close button is clicked"""
        self.Destroy()
      
class CreditsWindow(wx.Dialog):
    """Credits window"""
   
    def __init__(self, parent, id, title, pos=wx.DefaultPosition,
                size=wx.DefaultSize):
        wx.Dialog.__init__(self, parent, id, title, pos, size)
      
        vbox = wx.BoxSizer(wx.VERTICAL)
      
        nb = wx.Notebook(self, -1)
      
        # "Written by" panel
        writePanel = wx.Panel(nb, -1)
        vboxWrite = wx.BoxSizer(wx.VERTICAL)
        programmers = ("Vincent Kraeutler <vincent@etoy.com>", "Paul Kremer <pol@etoy.com>")
        writtenString = "\n".join(programmers)
        #written = enc.toWX(writtenString)
        labelWrite = wx.StaticText(writePanel, -1, writtenString)
        vboxWrite.Add(labelWrite, 0, wx.ALL, 10)
        writePanel.SetSizer(vboxWrite)
        writePanel.SetFocus()
      
        nb.AddPage(writePanel, _("Programmers"))

        # "Versions" panel
        versionsPanel = wx.Panel(nb, -1)
        vboxSP = wx.BoxSizer(wx.VERTICAL)
        pythonversion = "Python %s" % getPythonVersionString()
        wxversion = "wxPython " + ".".join( map( str, wx.VERSION ) )
        versions_list = [pythonversion, wxversion]
        versionsString = "\n".join(versions_list)
        #sponsor = enc.toWX(versionsString)
        labelSP = wx.StaticText(versionsPanel, -1, versionsString)
        vboxSP.Add(labelSP, 0, wx.ALL, 10)
        versionsPanel.SetSizer(vboxSP)
        nb.AddPage(versionsPanel, _("Versions"))
      
        vbox.Add(nb, 1, wx.ALL | wx.EXPAND, 3)
      
        buttonClose = wx.Button(self, 2005, _("&Close"))
        vbox.Add(buttonClose, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
      
        self.SetSizer(vbox)
      
        wx.EVT_BUTTON(self, 2005, self.onClose)

      
    def onClose(self, event):
        """This method is invoked when Close button is clicked"""
        self.Destroy()
