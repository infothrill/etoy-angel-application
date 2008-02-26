import os
import wx

from angel_app.gui.compat import wrap as platformwrap

class WelcomePanel(wx.Panel):
    def __init__(self, parent, statuslog):
        wx.Panel.__init__(self, parent, -1)
        Sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetBackgroundColour(wx.WHITE)
        bitmapfilename = os.path.join(platformwrap.getResourcePath(), "images", "angel_app_welcomescreen.jpg")
        assert os.path.isfile(bitmapfilename), "Welcome screen picture '%s' could not be found" % bitmapfilename
        bmp = wx.Bitmap(bitmapfilename, wx.BITMAP_TYPE_JPEG)
        pic = wx.StaticBitmap(self, -1, bmp, wx.Point(bmp.GetWidth(), bmp.GetHeight()))

        # adding stretchable space before and after centers the image.
        Sizer.Add((1,1),1)
        Sizer.Add(pic, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ADJUST_MINSIZE, 0)
        Sizer.Add((1,1),1)
   
        self.SetSizer(Sizer)
