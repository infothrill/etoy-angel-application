import os
import wx

from angel_app.gui.compat import wrap as platformwrap

class WelcomePanel(wx.Panel):
    def __init__(self, parent, statuslog):
        wx.Panel.__init__(self, parent, -1)
        Sizer = wx.BoxSizer(wx.HORIZONTAL)

        bmp = wx.Bitmap(os.path.join(platformwrap.getResourcePath(), "images", "angel_app_welcomescreen.jpg"), wx.BITMAP_TYPE_JPEG)
        pic = wx.StaticBitmap(self, -1, bmp, wx.Point(-1, -1))
        self.SetForegroundColour(wx.WHITE)
        self.SetBackgroundColour(wx.WHITE)

        Sizer.Add(pic, 0, wx.ALL | wx.CENTRE, 0)

        self.SetSizer(Sizer)

