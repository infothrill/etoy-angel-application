import wx

_ = wx.GetTranslation

class AngelStatusBar(wx.StatusBar):
    """
    Status bar for the main frame. Shows 2 things:
    - currently selected menu
    - p2p status (running/stopped)
    """
    def __init__(self, parent):
        """
        Initializes a timer to see if the p2p process is running.
        """
        self.p2p = wx.GetApp().p2p
        wx.StatusBar.__init__(self, parent, -1)

        # This status bar has one field
        self.SetFieldsCount(2)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-2,-1])

        # We're going to use a timer to drive a status of the p2p-process
        # in the last field.
        self.timer = wx.PyTimer(self.Notify)
        self.timer.Start(1001)
        self.Notify()

    def Notify(self):
        """
        Timer callback to check if the p2p process is running and
        set the status bar text accordingly.
        """
        if self.p2p.isAlive():
            status = _("p2p running")
        else:
            status = _("p2p stopped")
        self.SetStatusText(status, 1)


class StatusLog(object):
    """
    The log output is redirected to the status bar of the containing frame.
    """

    def WriteText(self,text_string):
        self.write(text_string)

    def write(self,text_string):
        wx.GetApp().GetTopWindow().SetStatusText(text_string)

